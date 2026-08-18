import plotly.graph_objects as go
import pandas as pd

def plot_equity_curve(results: dict):
    """
    Dummy plotting function for the backtest equity curve.
    Expects the results dictionary from run_backtest().
    """
    # Later this will parse the actual array of equity history returned by the backend
    print("Plotting Equity Curve (Placeholder)...")
    print(results)

def plot_signals(df: pd.DataFrame, position_col='position', price_col='close'):
    """
    Plot the price chart with Buy/Sell markers based on the position column.
    """
    fig = go.Figure()
    
    # Plot price
    fig.add_trace(go.Scatter(
        x=df.index if isinstance(df.index, pd.DatetimeIndex) else df['timestamp'],
        y=df[price_col],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=1)
    ))
    
    # Find signal transitions
    # Long when position changes to 1, Short when position changes to -1
    # This is a basic example; logic should match your specific signal definition
    pos = df[position_col]
    diff = pos.diff()
    
    buys = df[diff > 0]
    sells = df[diff < 0]
    
    fig.add_trace(go.Scatter(
        x=buys.index if isinstance(buys.index, pd.DatetimeIndex) else buys['timestamp'],
        y=buys[price_col],
        mode='markers',
        name='Buy',
        marker=dict(symbol='triangle-up', size=10, color='green')
    ))
    
    fig.add_trace(go.Scatter(
        x=sells.index if isinstance(sells.index, pd.DatetimeIndex) else sells['timestamp'],
        y=sells[price_col],
        mode='markers',
        name='Sell',
        marker=dict(symbol='triangle-down', size=10, color='red')
    ))
    
    fig.update_layout(title="Trading Signals", template='plotly_dark')
    fig.show()
