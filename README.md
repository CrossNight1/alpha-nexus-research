# AlphaNexusResearch

A Python research helper library for the Alpha Nexus platform. Designed specifically for Google Colab environments to seamlessly fetch historical data and execute vectorized backtests using the remote Alpha Nexus engine.

## Installation

```bash
pip install git+https://github.com/your-org/alpha-nexus-research.git
```

## Quick Start

```python
import AlphaNexusResearch as an

# Initialize connection
an.init(token="YOUR_SESSION_TOKEN")

# Fetch data
df = an.data.history(symbol="BTCUSDT", asset_class="crypto", interval="1h")

# Create simple signal (e.g., Buy and Hold)
df['position'] = 1

# Run vectorized backtest on the server
results = an.backtest.run_backtest(df)

# Visualize results
an.plot.plot_equity_curve(results)
```
