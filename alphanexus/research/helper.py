import pandas as pd
from typing import List, Union
from alphanexus.models import AssetData

def merge_data(assets: Union[AssetData, List[AssetData]], target_col: str = "close") -> pd.DataFrame:
    """
    Extracts a specific column from a list of AssetData objects and merges them into a single DataFrame.
    
    Args:
        assets (List[AssetData]): A list of AssetData objects to merge.
        target_col (str): The column to extract from each asset's data (e.g., 'close', 'open', 'volume').
                          Case-insensitive.
                          
    Returns:
        pd.DataFrame: A combined DataFrame with a datetime index. Columns are named by AssetData.Symbol.
    """
    if not isinstance(assets, list):
        assets = [assets]
        
    series_list = []
    for asset in assets:
        sym = asset.symbol.upper()
        
        # Make lookup case-insensitive
        cols = {str(c).lower(): c for c in asset.data.columns}
        target_lower = target_col.lower()
        
        if target_lower not in cols:
            raise KeyError(f"Column '{target_col}' not found in asset {sym}. Available columns: {list(asset.data.columns)}")
            
        real_col = cols[target_lower]
        
        series = asset.data[real_col].copy()
        
        # Ensure it has a datetime index for merging
        if 'datetime' in cols:
            series.index = asset.data[cols['datetime']]
        elif 'time' in cols:
            series.index = asset.data[cols['time']]
        elif 'timestamp' in cols:
            series.index = asset.data[cols['timestamp']]
            
        series.name = sym
        series_list.append(series)
        
    if not series_list:
        return pd.DataFrame()
        
    # Merge all series side-by-side using outer join on the index
    return pd.concat(series_list, axis=1)
