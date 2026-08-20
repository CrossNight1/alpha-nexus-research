# alphanexus

A Python research SDK for the **Alpha Nexus** platform. Designed for notebook environments (Google Colab, Jupyter) to seamlessly fetch historical data and execute vectorized backtests using the remote Alpha Nexus engine.

## Installation

```bash
pip install alphanexus
```

Or, to install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/CrossNight1/alpha-nexus-research.git
```

## Authentication

You can authenticate using your account credentials or a session token (legacy mode) from the Alpha Nexus UI.

```python
import alphanexus as an

# Option A: Login with Email/Password
an.login(email="YOUR_EMAIL", password="YOUR_PASSWORD")

# Option B: Initialize with a Session Token
an.init(token="YOUR_SESSION_TOKEN")

print("Connected to Alpha Nexus Research!")
```

---

## Quick Start

### Example 1: Multi-Asset Momentum Strategy

```python
import alphanexus as an
import alphanexus.research as anr
import pandas as pd
import numpy as np

# 1. Authenticate
an.login(email="user@example.com", password="password")

# 2. Fetch historical data
btc = anr.data.history("BTCUSDT", asset_class="crypto", interval="1d", exchange="binancefutures")
eth = anr.data.history("ETHUSDT", asset_class="crypto", interval="1d", exchange="binancefutures")
assets = [btc, eth]

# 3. Merge close prices into a single DataFrame
df_close = anr.helper.merge_data(assets, target_col="close")

# 4. Generate signals: go long if 30-day return > 0, short if < 0
momentum = df_close.pct_change(periods=30)
signals = pd.DataFrame(
    data=np.where(momentum > 0, 1.0, np.where(momentum < 0, -1.0, 0.0)),
    index=df_close.index,
    columns=df_close.columns
)
signals.iloc[:30] = 0.0  # Flat during lookback period

# 5. Bundle signals with asset metadata
position_series_list = [signals[a.symbol] for a in assets]
targets = anr.backtest.build_position(assets, position_series_list)

# 6. Run the backtest engine
results = anr.backtest.run(targets, capital=100000.0, broker="binancefutures")

# 7. View results
results.summary()
results.rolling_summary()
results.plot()
```

### Example 2: Single Asset SMA Crossover

```python
import alphanexus as an
import alphanexus.research as anr
import numpy as np
import pandas as pd

an.login(email="user@example.com", password="password")

btc = anr.data.history("BTCUSDT", asset_class="crypto", interval="1d", exchange="binancefutures")

close = btc.data["close"]
fast = close.rolling(20).mean()
slow = close.rolling(50).mean()

# 1 = Long, -1 = Short
position = np.where(fast > slow, 1.0, -1.0)
position_series = pd.Series(position, index=close.index).fillna(0.0)

target = anr.backtest.build_position(btc, position_series)
results = anr.backtest.run(target, capital=100000.0)

results.summary()
results.plot()
```

---

## API Reference

### `alphanexus.login(email, password, base_url)`
Initialize the global SDK client using credentials.
- `email` *(str)*: Your Alpha Nexus email.
- `password` *(str)*: Your Alpha Nexus password.
- `base_url` *(str, optional)*: API base URL. Defaults to `https://alpha-nexus.the20.sg`.

### `alphanexus.init(token, base_url)`
Initialize the global SDK client using a session token.
- `token` *(str)*: Your Alpha Nexus session token.
- `base_url` *(str, optional)*: API base URL. Defaults to `https://alpha-nexus.the20.sg`.

### `alphanexus.research.data.history(symbol, asset_class, interval, exchange)`
Fetch historical OHLCV data.
- Returns: `AssetData` dataclass with `.data` (DataFrame), `.info` (dict), and `.symbol` (str).

### `alphanexus.research.data.tradable_tickers(asset_class)`
List all available symbols for a given asset class.
- Returns: `list[dict]`

### `alphanexus.research.backtest.build_position(asset, position_series)`
Package asset metadata with a signal Series.
- Supports single or list of `AssetData` and `pd.Series`.
- Returns: `PositionTarget` or `list[PositionTarget]`.

### `alphanexus.research.backtest.run(positions, capital, broker, auto_normalize, timeout)`
Submit a vectorized backtest to the remote engine.
- `capital` *(float)*: Starting capital. Default `100000.0`.
- `broker` *(str)*: Fee model. Default `"backtest_default"`.
- `auto_normalize` *(bool)*: Auto-scale weights to sum to 1.0 daily. Default `True`.
- `timeout` *(int)*: Max seconds to wait. Default `300`.
- Returns: `VectorizedResult`.

### `VectorizedResult`
| Method / Attribute | Description |
|---|---|
| `.summary()` | Prints a table of performance statistics |
| `.rolling_summary()` | Returns a DataFrame of yearly rolling performance |
| `.plot(drop_series=[])` | Interactive 2-panel Plotly chart |
| `.strategy_equity` | Equity curve (pd.Series or pd.DataFrame) |
| `.drawdown` | Drawdown series |
| `.rolling_sharpe` | Rolling Sharpe ratio |
| `.rolling_beta` | Rolling Beta |

### `alphanexus.research.helper.merge_data(assets, target_col)`
Merge a column across multiple `AssetData` objects into a wide DataFrame.

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| Historical Data Fetch | 60 requests / minute |
| Backtest Submissions | 10 requests / minute |
| Concurrent Backtests | 1 at a time per user |

---

## License

MIT License © Alpha Nexus / The20.sg
