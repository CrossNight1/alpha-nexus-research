import io
import logging
import pandas as pd
from typing import Union, List, Optional
from alphanexus.client import Client
from alphanexus import get_default_client
from alphanexus.models import AssetData
from alphanexus.exceptions import APIConnectionError, AlphaNexusError

logger = logging.getLogger("alphanexus.research.data")

def history(
    symbol: Union[str, List[str]], 
    asset_class: str, 
    interval: str, 
    exchange: str = 'binance',
    client: Optional[Client] = None
) -> Union[AssetData, List[AssetData]]:
    """
    Fetch historical data from the Alpha Nexus Data Warehouse.
    
    Args:
        symbol (str or list of str): The trading symbol (e.g., 'BTCUSDT') or list of symbols.
        asset_class (str): The asset class (e.g., 'crypto', 'stocks').
        interval (str): Timeframe (e.g., '1h', '1d').
        exchange (str, optional): Exchange name (e.g., 'binance').
        client (Client, optional): Explicit client to use (defaults to global client).
        
    Returns:
        AssetData or List[AssetData]: An object containing metadata and historical OHLCV data.
    """
    if client is None:
        client = get_default_client()
        
    if isinstance(symbol, list):
        return [history(sym, asset_class, interval, exchange, client) for sym in symbol]
        
    endpoint = f"{client.base_url}/api/research/data"
    params = {
        "symbol": symbol,
        "asset_class": asset_class,
        "interval": interval,
        "exchange": exchange
    }
    
    logger.info(f"Fetching data for {symbol} ({interval})...")
    
    try:
        resp = client.session.get(endpoint, params=params, headers=client.get_auth_headers())
        
        if resp.status_code != 200:
            raise APIConnectionError(f"Failed to fetch data: {resp.status_code} - {resp.text}")
            
        df = pd.read_parquet(io.BytesIO(resp.content))
        return AssetData(info=params, data=df)
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        raise

def tradable_tickers(asset_class: str, client: Optional[Client] = None) -> List[dict]:
    """
    Fetch all tradable tickers for a specific asset class.
    
    Args:
        asset_class (str): The asset class (e.g., 'crypto', 'stocks').
        client (Client, optional): Explicit client to use.
        
    Returns:
        List[dict]: A list of dictionaries containing ticker metadata.
    """
    if client is None:
        client = get_default_client()
        
    endpoint = f"{client.base_url}/api/assets/{asset_class}/tradable_tickers"
    
    logger.info(f"Fetching tradable tickers for {asset_class}...")
    try:
        resp = client.session.get(endpoint, headers=client.get_auth_headers())
        
        if resp.status_code != 200:
            raise APIConnectionError(f"Failed to fetch tickers: {resp.status_code} - {resp.text}")
            
        data = resp.json()
        if data.get('status') == 'success':
            tickers = data.get('tickers', [])
            allowed_keys = {
                "symbol", "asset_class", "name", "exchange", 
                "timezone", "calendar", "currency", "region", 
                "backtest_resolutions"
            }
            results = []
            for t in tickers:
                filtered = {}
                for k, v in t.items():
                    if k == "exchange":
                        filtered["broker_id"] = v
                    elif k in allowed_keys and k != "exchange":
                        filtered[k] = v
                results.append(filtered)
            return results
        else:
            raise AlphaNexusError(f"Error fetching tickers: {data}")
    except Exception as e:
        logger.error(f"Error fetching tradable tickers: {e}")
        raise

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
