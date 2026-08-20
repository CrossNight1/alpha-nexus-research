import pandas as pd
import requests
import io
from .config import get_token, get_base_url

from .core import AssetData
from typing import Union, List

def history(symbol: Union[str, List[str]], asset_class: str, interval: str, exchange: str = 'binance') -> Union[AssetData, List[AssetData]]:
    """
    Fetch historical data from the Alpha Nexus Data Warehouse.
    
    Args:
        symbol (str or list of str): The trading symbol (e.g., 'BTCUSDT') or list of symbols.
        asset_class (str): The asset class (e.g., 'crypto', 'stocks').
        interval (str): Timeframe (e.g., '1h', '1d').
        exchange (str, optional): Exchange name (e.g., 'binance').
        
    Returns:
        AssetData or List[AssetData]: An object containing metadata and historical OHLCV data.
    """
    if isinstance(symbol, list):
        return [history(sym, asset_class, interval, exchange) for sym in symbol]

    base_url = get_base_url()
    token = get_token()
    
    endpoint = f"{base_url}/api/research/data"
    params = {
        "symbol": symbol,
        "asset_class": asset_class,
        "interval": interval,
        "exchange": exchange
    }
        
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Fetching data for {symbol} ({interval})...")
    resp = requests.get(endpoint, params=params, headers=headers)
    
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch data: {resp.status_code} - {resp.text}")
        
    df = pd.read_parquet(io.BytesIO(resp.content))
    return AssetData(info=params, data=df)

def tradable_tickers(asset_class: str) -> List[dict]:
    """
    Fetch all tradable tickers for a specific asset class.
    
    Args:
        asset_class (str): The asset class (e.g., 'crypto', 'stocks').
        
    Returns:
        List[dict]: A list of dictionaries containing ticker metadata.
    """
    base_url = get_base_url()
    endpoint = f"{base_url}/api/assets/{asset_class}/tradable_tickers"
    
    print(f"Fetching tradable tickers for {asset_class}...")
    resp = requests.get(endpoint)
    
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch tickers: {resp.status_code} - {resp.text}")
        
    data = resp.json()
    if data.get('status') == 'success':
        tickers = data.get('tickers', [])
        
        # Filter keys
        allowed_keys = {
            "symbol", "asset_class", "name", "exchange", 
            "timezone", "calendar", "currency", "region", 
            "backtest_resolutions"
        }
        
        filtered_tickers = []
        for t in tickers:
            filtered = {k: v for k, v in t.items() if k in allowed_keys}
            filtered_tickers.append(filtered)
            
        return filtered_tickers
    else:
        raise Exception(f"Error fetching tickers: {data}")
