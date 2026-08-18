import pandas as pd
import requests
import io
import time
import json
from .config import get_token, get_base_url
from .core import AssetData, PositionTarget, VectorizedResult

from typing import Union, List

def build_position(asset: Union[AssetData, List[AssetData]], position_series: Union[pd.Series, List[pd.Series]]) -> Union[PositionTarget, List[PositionTarget]]:
    """
    Package metadata with target positions.
    Supports single AssetData and pd.Series, or lists of AssetData and pd.Series.
    """
    if isinstance(asset, list) and isinstance(position_series, list):
        if len(asset) != len(position_series):
            raise ValueError("Length of assets and position_series must match.")
        
        targets = []
        for a, s in zip(asset, position_series):
            if not isinstance(s, pd.Series):
                raise ValueError(f"Positions for {a.info.get('symbol')} must be a Pandas Series.")
            targets.append(PositionTarget(a.info, s))
        return targets
        
    if not isinstance(position_series, pd.Series):
        raise ValueError("Positions must be a Pandas Series.")
    
    return PositionTarget(asset.info, position_series)

def run(positions, capital: float = 100000.0, broker: str = "binance", auto_normalize: bool = True) -> dict:
    """
    Run a vectorized backtest on the remote Alpha Nexus Go-Engine.
    
    Args:
        positions: A single PositionTarget or a list of PositionTargets.
        capital: Initial capital for the backtest.
        broker: Broker fee/slippage model identifier.
        auto_normalize: If True, dynamically scales weights so the total absolute exposure per day is exactly 1.0.
                           
    Returns:
        dict: Backtest metrics and results returned by the server.
    """
    token = get_token()
    base_url = get_base_url()
    
    if not isinstance(positions, list):
        positions = [positions]
        
    if len(positions) == 0:
        raise ValueError("Positions list cannot be empty.")

    print(f"Preparing Vectorized Backtest for {len(positions)} assets...")

    # 1. Gather config
    feeds_config = [p.info for p in positions]
    config_dict = {
        "capital": capital,
        "broker": broker,
        "feeds": feeds_config
    }
    
    # 2. Build Wide-Format Matrix
    series_list = []
    for p in positions:
        sym = p.info['symbol'].upper()
        series_list.append(p.positions.rename(sym))
        
    combined_df = pd.concat(series_list, axis=1)
    
    if auto_normalize:
        # Sum the absolute weights for each day
        row_sums = combined_df.abs().sum(axis=1)
        # Divide each day's weights by the sum to scale to 1.0 (avoiding divide-by-zero)
        combined_df = combined_df.div(row_sums.replace(0, 1), axis=0)
    
    # Ensure index is named timestamp for the Arrow loader
    if combined_df.index.name not in ['timestamp', 'time']:
        combined_df.index.name = 'timestamp'
        
    combined_df.reset_index(inplace=True)

    # 3. Serialize to Parquet
    buffer = io.BytesIO()
    combined_df.to_parquet(buffer, index=False)
    buffer.seek(0)
    
    # 4. Upload to API Gateway
    endpoint = f"{base_url}/api/research/backtest"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("Uploading wide-format weight matrix to Server...")
    resp = requests.post(
        endpoint,
        headers=headers,
        data={'config': json.dumps(config_dict)},
        files={'file': ('signal.parquet', buffer, 'application/octet-stream')}
    )
    
    if resp.status_code != 200:
        raise Exception(f"Backtest launch failed: {resp.text}")
        
    launch_data = resp.json()
    session_id = launch_data.get('session_id')
    print(f"Engine launched successfully. Session ID: {session_id}")
    
    # 5. Poll for completion
    print("Waiting for results...")
    metrics_endpoint = f"{base_url}/api/runs/{session_id}/metrics"
    status_endpoint = f"{base_url}/api/runs/{session_id}/status"
    
    while True:
        try:
            status_resp = requests.get(status_endpoint, headers=headers)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get('status')
                if status in ['completed', 'failed', 'crashed']:
                    if status != 'completed':
                        raise Exception(f"Backtest {status}")
                        
                    # Fetch metrics
                    metrics_resp = requests.get(metrics_endpoint, headers=headers)
                    if metrics_resp.status_code == 200:
                        return VectorizedResult(metrics_resp.json())
                    else:
                        raise Exception(f"Failed to fetch metrics: {metrics_resp.text}")
        except Exception as e:
            if "Backtest failed" in str(e) or "Backtest crashed" in str(e):
                raise
            # Ignore network transient errors while polling, but print it if it's a code error
            if not isinstance(e, (requests.exceptions.RequestException, json.JSONDecodeError)):
                print(f"Polling error: {e}")
            pass
            
        time.sleep(0.5)        
    raise TimeoutError("Backtest polling timed out after 300 seconds.")
