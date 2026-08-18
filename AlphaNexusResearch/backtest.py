import pandas as pd
import requests
import io
from .config import get_token, get_base_url

def run_backtest(df: pd.DataFrame) -> dict:
    """
    Run a vectorized backtest on the remote Alpha Nexus Go-Engine.
    
    Args:
        df (pd.DataFrame): The input DataFrame. Must contain 'timestamp', 'price' (or 'close'), and 'position'.
                           'position' should be a numeric column ranging from -1 (Short) to 1 (Long).
                           
    Returns:
        dict: Backtest metrics and results returned by the server.
    """
    token = get_token()
    base_url = get_base_url()
    
    # 1. Validation
    required_cols = ['position']
    if 'position' not in df.columns:
        raise ValueError("DataFrame must contain a 'position' column with values [-1, 1].")
        
    price_col = 'price' if 'price' in df.columns else ('close' if 'close' in df.columns else None)
    if not price_col:
        raise ValueError("DataFrame must contain a 'price' or 'close' column.")
        
    ts_col = 'timestamp' if 'timestamp' in df.columns else ('time' if 'time' in df.columns else None)
    if not ts_col and df.index.name not in ['timestamp', 'time'] and not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a 'timestamp' column or a DatetimeIndex.")
        
    # 2. Extract necessary columns
    extract_cols = [price_col, 'position']
    if ts_col:
        extract_cols.insert(0, ts_col)
        df_upload = df[extract_cols].copy()
    else:
        df_upload = df[extract_cols].copy()
        df_upload['timestamp'] = df.index
        
    # Standardize names
    df_upload.rename(columns={price_col: 'price'}, inplace=True)
    
    # 3. Serialize to Parquet Bytes
    print("Optimizing and serializing data payload (Parquet)...")
    buffer = io.BytesIO()
    df_upload.to_parquet(buffer, index=False)
    buffer.seek(0)
    
    # 4. Upload to Server
    endpoint = f"{base_url}/api/research/backtest"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("Uploading to Alpha Nexus server for Vectorized Execution...")
    files = {
        'file': ('backtest_data.parquet', buffer, 'application/octet-stream')
    }
    
    resp = requests.post(endpoint, headers=headers, files=files)
    
    if resp.status_code != 200:
        raise Exception(f"Backtest execution failed: {resp.status_code} - {resp.text}")
        
    print("Backtest completed successfully!")
    return resp.json()
