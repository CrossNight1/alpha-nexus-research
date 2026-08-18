import pandas as pd
import numpy as np

# 1. Import and Initialize
import AlphaNexusResearch
# Put your token here to test live endpoints
AlphaNexusResearch.init(token='YtGKhguP5aZlDCBHQk-JeqOHbnZh-DVx', base_url='https://alpha-nexus.the20.sg')

from AlphaNexusResearch import data, backtest, helper

print("Fetching historical data for BTC & ETH...")
btc, eth = data.history(['BTCUSDT', 'ETHUSDT'], asset_class='crypto', interval='1d', exchange='binancefutures')

print("\n[TEST 1] Testing helper.merge_data()...")
df_close = helper.merge_data([btc, eth], target_col="close")
print(df_close.tail(3))

print("\n[TEST 2] Testing build_position() with multiple assets...")
btc_signals = pd.Series(np.random.choice([0.0, 1.0], size=len(btc.data)), index=btc.data['datetime'])
eth_signals = pd.Series(np.random.choice([-1.0, 0.0, 1.0], size=len(eth.data)), index=eth.data['datetime'])

multi_targets = backtest.build_position([btc, eth], [btc_signals, eth_signals])
print(f"Successfully built {len(multi_targets)} PositionTargets!")

print("\n[TEST 3] Testing backtest.run()...")
results = backtest.run(positions=multi_targets, auto_normalize=True)
print("\nAvailable Attributes:")
print(results)

# We can't render interactive charts easily in the terminal, so we will save it to an HTML file to verify
print("\n[TEST 4] Testing results.plot()...")
import plotly.io as pio
pio.renderers.default = "json"  # Prevents crash in headless terminal

# This will build the Plotly figure but won't open a browser window
results.plot(drop_series=['daily_weights'])
print("Plot built successfully (Skipping browser render in CLI)!")
