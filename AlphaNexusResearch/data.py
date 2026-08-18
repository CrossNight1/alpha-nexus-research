import pandas as pd
import requests
import io
from .config import get_token, get_base_url

def history(symbol: str, asset_class: str, interval: str, exchange: str = None) -> pd.DataFrame:
    """
    Fetch historical data from the Alpha Nexus Data Warehouse.
    
    Args:
        symbol (str): The trading symbol (e.g., 'BTCUSDT').
        asset_class (str): The asset class (e.g., 'crypto', 'stocks').
        interval (str): Timeframe (e.g., '1h', '1d').
        exchange (str, optional): Exchange name (e.g., 'binance').
        
    Returns:
        pd.DataFrame: A Pandas DataFrame containing the historical OHLCV data.
    """
    base_url = get_base_url()
    token = get_token()
    
    endpoint = f"{base_url}/api/research/data"
    params = {
        "symbol": symbol,
        "asset_class": asset_class,
        "interval": interval
    }
    if exchange:
        params["exchange"] = exchange
        
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Fetching data for {symbol} ({interval})...")
    resp = requests.get(endpoint, params=params, headers=headers)
    
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch data: {resp.status_code} - {resp.text}")
        
    # Load binary parquet stream directly to DataFrame
    return pd.read_parquet(io.BytesIO(resp.content))
