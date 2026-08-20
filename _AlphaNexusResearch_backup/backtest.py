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

def run(positions, capital: float = 100000.0, broker: str = "backtest_default", auto_normalize: bool = True, timeout: int = 300, apply_signal_shift: bool = True) -> dict:
    """
    Run a vectorized backtest on the remote Alpha Nexus Go-Engine.
    
    Args:
        positions: A single PositionTarget or a list of PositionTargets.
        capital: Initial capital for the backtest.
        broker: Broker fee/slippage model identifier.
        auto_normalize: If True, dynamically scales weights so the total absolute exposure per day is exactly 1.0.
        timeout: Maximum seconds to wait for the backtest to complete. Defaults to 300 seconds.
        apply_signal_shift: If True (default), shifts the entire position matrix forward by 1 bar before
                            submitting to the engine. This prevents look-ahead bias — signals computed
                            using close[t] will only take effect at bar t+1 (the open the engine executes at).
                            Set to False ONLY if you have already applied .shift(1) to your signals manually.
                           
    Returns:
        VectorizedResult: Backtest results object with metrics and chart data.
    
    Raises:
        TimeoutError: If the backtest does not complete within the specified timeout.
        RuntimeError: If the server reports the backtest as failed or crashed.
        Exception: If the backtest launch or metric fetch fails.
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
    
    if apply_signal_shift:
        # Shift signals forward by 1 bar to prevent look-ahead bias.
        # The engine executes at the open of the NEXT bar, so position[t] should only
        # use information available at close[t-1]. Without this shift, any signal that
        # reads close[t] to decide position[t] is peeking into the future.
        combined_df = combined_df.shift(1).fillna(0.0)
    
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
    
    if resp.status_code == 429:
        raise RuntimeError(f"Rate limit exceeded or a backtest is already running: {resp.json().get('detail', resp.text)}")
    
    if resp.status_code != 200:
        raise Exception(f"Backtest launch failed ({resp.status_code}): {resp.text}")
        
    launch_data = resp.json()
    session_id = launch_data.get('session_id')
    print(f"Engine launched successfully. Session ID: {session_id}")
    
    # 5. Poll for completion with a hard timeout
    print("Waiting for results...")
    metrics_endpoint = f"{base_url}/api/runs/{session_id}/metrics"
    status_endpoint = f"{base_url}/api/runs/{session_id}/status"
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status_resp = requests.get(status_endpoint, headers=headers, timeout=10)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get('status')
                if status in ['completed', 'failed', 'crashed']:
                    if status != 'completed':
                        raise RuntimeError(f"Backtest {status}. Please check your strategy code and try again.")
                        
                    # Fetch metrics
                    metrics_resp = requests.get(metrics_endpoint, headers=headers, timeout=10)
                    if metrics_resp.status_code == 200:
                        return VectorizedResult(metrics_resp.json())
                    else:
                        raise Exception(f"Failed to fetch metrics: {metrics_resp.text}")
        except RuntimeError:
            raise  # Don't swallow terminal errors (failed/crashed)
        except Exception as e:
            # Ignore transient network errors while polling
            pass
            
        time.sleep(1)
    
    raise TimeoutError(f"Backtest did not complete within {timeout} seconds. You can increase the timeout by passing `timeout=<seconds>` to backtest.run().")
