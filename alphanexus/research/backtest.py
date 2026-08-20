import io
import time
import json
import logging
import pandas as pd
from typing import Union, List, Optional
from alphanexus.client import Client
from alphanexus import get_default_client
from alphanexus.models import AssetData, PositionTarget, VectorizedResult
from alphanexus.exceptions import AlphaNexusError, APIConnectionError, BacktestTimeoutError

logger = logging.getLogger("alphanexus.research.backtest")

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
                raise ValueError(f"Positions for {a.symbol} must be a Pandas Series.")
            targets.append(PositionTarget(a.info, s))
        return targets
        
    if not isinstance(position_series, pd.Series):
        raise ValueError("Positions must be a Pandas Series.")
    
    return PositionTarget(asset.info, position_series)

def run(positions: Union[PositionTarget, List[PositionTarget]], 
        capital: float = 100000.0, 
        broker: str = "backtest_default", 
        auto_normalize: bool = True, 
        timeout: int = 300, 
        apply_signal_shift: bool = True,
        client: Optional[Client] = None) -> VectorizedResult:
    """
    Run a vectorized backtest on the remote Alpha Nexus Go-Engine.
    
    Args:
        positions: A single PositionTarget or a list of PositionTargets.
        capital: Initial capital for the backtest.
        broker: Broker fee/slippage model identifier.
        auto_normalize: If True, dynamically scales weights so total absolute exposure per day is exactly 1.0.
        timeout: Maximum seconds to wait for the backtest to complete. Defaults to 300 seconds.
        apply_signal_shift: If True (default), shifts the entire position matrix forward by 1 bar to prevent look-ahead bias.
        client (Client, optional): Explicit client to use (defaults to global client).
                           
    Returns:
        VectorizedResult: Backtest results object with metrics and chart data.
    """
    if client is None:
        client = get_default_client()
        
    if not isinstance(positions, list):
        positions = [positions]
        
    if len(positions) == 0:
        raise ValueError("Positions list cannot be empty.")

    logger.info(f"Preparing Vectorized Backtest for {len(positions)} assets...")

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
        sym = p.info.get('symbol', 'UNKNOWN').upper()
        series_list.append(p.positions.rename(sym))
        
    combined_df = pd.concat(series_list, axis=1)
    
    if apply_signal_shift:
        combined_df = combined_df.shift(1).fillna(0.0)
    
    if auto_normalize:
        row_sums = combined_df.abs().sum(axis=1)
        combined_df = combined_df.div(row_sums.replace(0, 1), axis=0)
    
    if combined_df.index.name not in ['timestamp', 'time']:
        combined_df.index.name = 'timestamp'
        
    combined_df.reset_index(inplace=True)

    # 3. Serialize to Parquet
    buffer = io.BytesIO()
    combined_df.to_parquet(buffer, index=False)
    buffer.seek(0)
    
    # 4. Upload to API Gateway
    endpoint = f"{client.base_url}/api/research/backtest"
    headers = client.get_auth_headers()
    
    logger.info("Uploading wide-format weight matrix to Server...")
    resp = client.session.post(
        endpoint,
        headers=headers,
        data={'config': json.dumps(config_dict)},
        files={'file': ('signal.parquet', buffer, 'application/octet-stream')}
    )
    
    if resp.status_code == 429:
        raise AlphaNexusError(f"Rate limit exceeded or a backtest is already running: {resp.json().get('detail', resp.text)}")
    
    if resp.status_code != 200:
        raise APIConnectionError(f"Backtest launch failed ({resp.status_code}): {resp.text}")
        
    launch_data = resp.json()
    session_id = launch_data.get('session_id')
    logger.info(f"Engine launched successfully. Session ID: {session_id}")
    
    # 5. Poll for completion with a hard timeout
    logger.info("Waiting for results...")
    metrics_endpoint = f"{client.base_url}/api/runs/{session_id}/metrics"
    status_endpoint = f"{client.base_url}/api/runs/{session_id}/status"
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status_resp = client.session.get(status_endpoint, headers=headers, timeout=10)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get('status')
                if status in ['completed', 'failed', 'crashed']:
                    if status != 'completed':
                        raise AlphaNexusError(f"Backtest {status}. Please check your strategy code and try again.")
                        
                    metrics_resp = client.session.get(metrics_endpoint, headers=headers, timeout=10)
                    if metrics_resp.status_code == 200:
                        return VectorizedResult(metrics_resp.json())
                    else:
                        raise APIConnectionError(f"Failed to fetch metrics: {metrics_resp.text}")
        except AlphaNexusError:
            raise  # Terminal errors
        except Exception:
            pass   # Transient errors
            
        time.sleep(1)
    
    raise BacktestTimeoutError(f"Backtest did not complete within {timeout} seconds.")

def supported_brokers(client: Optional[Client] = None) -> List[dict]:
    """
    Fetch all supported brokers and their info.
    
    Args:
        client (Client, optional): Explicit client to use.
        
    Returns:
        List[dict]: A list of dictionaries containing broker metadata.
    """
    if client is None:
        client = get_default_client()
        
    endpoint = f"{client.base_url}/api/brokers"
    
    logger.info("Fetching supported brokers...")
    try:
        resp = client.session.get(endpoint, headers=client.get_auth_headers())
        
        if resp.status_code != 200:
            raise APIConnectionError(f"Failed to fetch brokers: {resp.status_code} - {resp.text}")
            
        data = resp.json()
        if data.get('status') == 'success':
            return data.get('brokers', [])
        else:
            raise AlphaNexusError(f"Error fetching brokers: {data}")
    except Exception as e:
        logger.error(f"Error fetching supported brokers: {e}")
        raise
