# alphanexus API Reference & User Guide

`alphanexus` is a Python SDK designed for notebook environments (like Google Colab or local Jupyter) that enables quantitative researchers to interact with the Alpha Nexus platform remotely. It provides tools to fetch historical data, generate vectorized signals using `pandas`/`numpy`, and execute highly scalable server-side backtests.

---

## 1. Initialization

You can initialize the SDK connection using either your account credentials or a session token (legacy mode). Must be called before using any other functions.

### Option A: `alphanexus.login(email, password, base_url)`
**Arguments:**
- `email` (str): Your Alpha Nexus account email.
- `password` (str): Your Alpha Nexus password.
- `base_url` (str): The base URL (e.g., `https://alpha-nexus.the20.sg`).

### Option B: `alphanexus.init(token, base_url)`
**Arguments:**
- `token` (str): Your Alpha Nexus session token.
- `base_url` (str): The base URL (e.g., `https://alpha-nexus.the20.sg`).

**Example:**
```python
import alphanexus as an
import alphanexus.research as anr

# Using Session Token
an.init(token="YOUR_SESSION_TOKEN")

# OR Using Email/Password
# an.login(email="user@example.com", password="password")
```

---

## 2. Data Module (`alphanexus.research.data`)

### `data.history(symbol, asset_class, interval, exchange)`
Fetches historical market data for one or multiple tickers.

**Arguments:**
- `symbol` (str | List[str]): A single ticker (e.g., `'BTCUSDT'`) or a list of tickers (e.g., `['BTCUSDT', 'ETHUSDT']`).
- `asset_class` (str): The asset class (e.g., `'crypto'`, `'stocks'`).
- `interval` (str): The timeframe resolution (e.g., `'1d'`, `'1h'`, `'15m'`).
- `exchange` (str): The exchange platform (e.g., `'binancefutures'`, `'alpaca'`).

**Returns:**
- Returns an `AssetData` dataclass (or a list of `AssetData` objects if a list of symbols was passed).
- Each `AssetData` object contains:
  - `asset.symbol` (str): The symbol of the asset.
  - `asset.info` (dict): Asset metadata (exchange, interval, etc.)
  - `asset.data` (pd.DataFrame): Historical OHLCV dataframe.

**Example:**
```python
import alphanexus.research as anr

btc, eth = anr.data.history(['BTCUSDT', 'ETHUSDT'], asset_class='crypto', interval='1d', exchange='binancefutures')
print(btc.data.head())
```

### `data.tradable_tickers(asset_class)`
Retrieves a list of all tradable tickers supported by the platform for a given asset class.

**Arguments:**
- `asset_class` (str): The asset class (e.g., `'crypto'`).

**Returns:**
- `List[dict]`: A list of dictionaries containing metadata for each tradable asset.

**Example:**
```python
tickers = anr.data.tradable_tickers('crypto')
print([t['symbol'] for t in tickers])
```

---

## 3. Helper Module (`alphanexus.research.helper`)

### `helper.merge_data(assets, target_col)`
A powerful utility to horizontally merge a specific column from multiple `AssetData` objects into a single wide-format DataFrame. This is crucial for **cross-sectional/vectorized** signal generation (e.g., momentum across 50 assets).

**Arguments:**
- `assets` (List[AssetData]): A list of `AssetData` objects fetched via `anr.data.history()`.
- `target_col` (str, default='close'): The OHLCV column to extract from each asset's data.

**Returns:**
- `pd.DataFrame`: A time-indexed DataFrame where each column corresponds to an asset's symbol.

**Example:**
```python
# Merge all 'close' prices into a single dataframe
df_close = anr.helper.merge_data([btc, eth], target_col='close')
# df_close now has columns: 'BTCUSDT', 'ETHUSDT'

# Vectorized signal generation across all assets instantly
momentum = df_close.pct_change(30)
signals = np.where(momentum > 0, 1.0, 0.0)
signals_df = pd.DataFrame(signals, index=df_close.index, columns=df_close.columns)
```

---

## 4. Backtest Module (`alphanexus.research.backtest`)

### `backtest.build_position(asset, position_series)`
Bundles your raw Pandas Series containing target positions (weights or signal values) with the corresponding asset metadata, preparing it for the backtest engine.

**Arguments:**
- `asset` (AssetData | List[AssetData]): The asset(s) metadata object.
- `position_series` (pd.Series | List[pd.Series]): A time-series indicating your desired position size/weight.
  - `1.0` means 100% long, `-0.5` means 50% short, `0.0` means flat.

**Returns:**
- `PositionTarget` (or `List[PositionTarget]`): An internal dataclass ready to be fed to `backtest.run()`.

**Example:**
```python
# Bulk build targets by iterating over the dataframe columns
position_series_list = [signals_df[asset.symbol] for asset in assets]
multi_targets = anr.backtest.build_position(assets, position_series_list)
```

### `backtest.run(positions, capital, broker, auto_normalize)`
Submits the `PositionTarget` objects to the Alpha Nexus backend engine for vectorized execution.

**Arguments:**
- `positions` (PositionTarget | List[PositionTarget]): The targets generated from `build_position()`.
- `capital` (float, default=100000.0): The starting portfolio equity.
- `broker` (str, default="backtest_default"): The broker configuration ID to use for realistic fee/slippage calculation (e.g., `'binance_futures'`).
- `auto_normalize` (bool, default=True): If `True`, the engine will automatically scale down position sizes proportionally if the sum of absolute weights exceeds `1.0` (100% equity). E.g., if you request 100% BTC and 100% ETH, the engine executes 50% BTC and 50% ETH to prevent margin rejection.

**Returns:**
- `VectorizedResult`: An object containing the backtest statistics, time-series arrays, and interactive plotting capabilities.

**Example:**
```python
results = anr.backtest.run(positions=multi_targets, broker="binance_futures", auto_normalize=True)
```

---

## 5. Result Visualization (`VectorizedResult`)

The `VectorizedResult` object returned by `backtest.run()` provides immediate access to performance metrics and charts.

### `results.summary()`
Prints a comprehensive statistics table in the notebook (CAGR, Sharpe, Drawdown, Win Rate, Alpha, Beta, etc.).

### `results.rolling_summary()`
Returns a `pd.DataFrame` containing the yearly rolling performance breakdown. Useful for evaluating the strategy's consistency over time.

### `results.plot(drop_series=None)`
Renders an interactive, dual-panel Plotly chart directly in the notebook.
- **Top Panel:** Displays Strategy Equity, Gross Equity, and Benchmark curves.
- **Bottom Panel:** A dropdown menu allowing you to inspect:
  - Daily Drawdown
  - Portfolio Exposure %
  - Portfolio Turnover
  - Daily Asset Weights
  - Cumulative Trading Fees
  - Rolling Sharpe / Beta
  
**Arguments:**
- `drop_series` (List[str], optional): Specify trace keys you want to hide from the dropdown (e.g., `drop_series=['daily_weights']`).

**Raw Time-Series Access:**
You can directly access raw data arrays via properties:
- `results.strategy_equity`
- `results.drawdown`
- `results.portfolio_turnover`
- `results.daily_weights` (A `pd.DataFrame` showing each asset's weight over time).
