# AlphaNexusResearch

A Python research helper library for the Alpha Nexus platform. Designed for notebook environments to seamlessly fetch historical data and execute vectorized backtests using the remote Alpha Nexus engine.

## Installation

```bash
pip install git+https://github.com/CrossNight1/alpha-nexus-research.git
```

## Quick Start: Single Asset & Multi-Asset Backtesting

Alpha Nexus Research uses a vectorized approach. You compute signals over historical data using pandas/numpy, bundle them with asset metadata via `build_position()`, and submit them to the remote engine.

### Example 1: Multi-Asset Momentum with `helper.merge_data`

```python
import AlphaNexusResearch
import pandas as pd
import numpy as np

# 1. Initialize Connection
AlphaNexusResearch.init(token="YOUR_SESSION_TOKEN", base_url='https://alpha-nexus.the20.sg')
from AlphaNexusResearch import data, backtest, helper
print('Connected to Alpha Nexus Research!')

# 2. Fetch Historical Data
print("Fetching Data...")
btc = data.history('BTCUSDT', asset_class='crypto', interval='1d', exchange='binancefutures')
eth = data.history('ETHUSDT', asset_class='crypto', interval='1d', exchange='binancefutures')
assets = [btc, eth]

# 3. Generate Signals (Vectorized using merge_data)
lookback_window = 30

# Merge the "close" columns of all assets into a single DataFrame
# The columns will automatically be named after the asset symbols (BTCUSDT, ETHUSDT)
df_close = helper.merge_data(assets, target_col='close')

# Calculate 30-day returns for ALL assets at the same time
momentum = df_close.pct_change(periods=lookback_window)

# Generate positions: 1.0 (Long) if > 0, -1.0 (Short) if < 0, else 0.0
signals = np.where(momentum > 0, 1.0, np.where(momentum < 0, -1.0, 0.0))

# Convert the raw NumPy array back to a Pandas DataFrame
signals_df = pd.DataFrame(signals, index=df_close.index, columns=df_close.columns)

# Flat (0.0) during the initial lookback period
signals_df.iloc[:lookback_window] = 0.0

# 4. Bundle signals alongside their asset metadata
# We extract each column back into a list of Series to feed into build_position
position_series_list = [signals_df[asset.info['symbol']] for asset in assets]

multi_targets = backtest.build_position(assets, position_series_list)
print(f"Successfully built {len(multi_targets)} PositionTargets!")

# 5. Run the Engine
print("Running Backtest Engine...")
results = backtest.run(positions=multi_targets, broker="binance_futures", auto_normalize=True)

# 6. Display Stats & Plot results
print("\nFinal Results:")
print(results)

# View statistics table
results.summary()

# View rolling yearly performance summary
results.rolling_summary()

# Plot interactive charts
results.plot(drop_series=['daily_weights'])
```

### Example 2: Per-Asset Signal Generation (Functional Approach)

```python
import AlphaNexusResearch
import pandas as pd
import numpy as np

# 1. Initialize
AlphaNexusResearch.init(token="YOUR_SESSION_TOKEN", base_url='https://alpha-nexus.the20.sg')
from AlphaNexusResearch import data, backtest
print('Connected to Alpha Nexus Research!')

# 2. Fetch Historical Data
print("Fetching Data...")
btc = data.history('BTCUSDT', asset_class='crypto', interval='1d', exchange='binancefutures')
eth = data.history('ETHUSDT', asset_class='crypto', interval='1d', exchange='binancefutures')

# 3. Generate Signals (30-Day Absolute Momentum)
lookback_window = 30

def calc_abs_momentum(df: pd.DataFrame, lookback: int) -> pd.Series:
    """Calculates Absolute Momentum (Long if positive, Short if negative)"""
    # Calculate price change over the lookback window
    momentum = df['close'].pct_change(periods=lookback)
    
    # Generate positions: 1.0 (Long) if momentum > 0, else -1.0 (Short) if momentum < 0, else 0.0
    signals = np.where(momentum > 0, 1.0, np.where(momentum < 0, -1.0, 0.0))
    pos_series = pd.Series(signals, index=df['datetime'])
    
    # Flat (0.0) during the initial lookback period when data is NaN
    pos_series.iloc[:lookback] = 0.0
    
    return pos_series

btc_pos_series = calc_abs_momentum(btc.data, lookback_window)
eth_pos_series = calc_abs_momentum(eth.data, lookback_window)

# 4. Bundle signals alongside their asset metadata using bulk API
multi_targets = backtest.build_position([btc, eth], [btc_pos_series, eth_pos_series])
print(f"Successfully built {len(multi_targets)} PositionTargets!")

# 5. Run the Engine
print("Running Backtest Engine...")
results = backtest.run(positions=multi_targets, auto_normalize=True)

# 6. Display Stats & Plot results
print("\nFinal Results:")
print(results)
results.plot(drop_series=['daily_weights'])
```
