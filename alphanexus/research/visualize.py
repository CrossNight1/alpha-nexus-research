import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def plot_results(results, drop_series=None):
    """
    Plots a 2-panel interactive chart:
      - Main Panel: Strategy Equity
      - Sub Panel: A dropdown-switchable chart of other metrics (Drawdown, Exposure, etc.)
    """
    if drop_series is None:
        drop_series = []
        
    # Define available sub-metrics
    sub_metrics = {
        'Drawdown': results.drawdown,
        'Portfolio Turnover': results.portfolio_turnover,
        'Rolling Sharpe': results.rolling_sharpe,
        'Rolling Beta': results.rolling_beta,
        'Exposure': results.exposure,
        'Trading Fees': results.trading_fees,
        'Daily Weights': results.daily_weights
    }
    
    # Filter out empty or dropped metrics
    valid_metrics = {}
    for name, data in sub_metrics.items():
        # Check if user wants to drop it or if it's empty
        is_dropped = any(d.lower() in name.lower() for d in drop_series)
        is_empty = False
        if isinstance(data, pd.DataFrame) and data.empty:
            is_empty = True
        elif isinstance(data, pd.Series) and data.empty:
            is_empty = True
        elif isinstance(data, (dict, list)) and not data:
            is_empty = True
            
        if not is_dropped and not is_empty:
            # specifically for Exposure, only show Exposure Ratio if it exists
            if name == 'Exposure' and isinstance(data, pd.DataFrame):
                if 'Exposure Ratio' in data.columns:
                    data = data[['Exposure Ratio']]
            # specifically for Trading Fees, only show Cumulative Fee if it exists
            elif name == 'Trading Fees' and isinstance(data, pd.DataFrame):
                cum_col = next((c for c in data.columns if 'cumulative' in c.lower()), None)
                if cum_col:
                    data = data[[cum_col]]
                    
            valid_metrics[name] = data
            
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        row_heights=[0.7, 0.3], vertical_spacing=0.05,
                        subplot_titles=('Strategy Equity', list(valid_metrics.keys())[0] if valid_metrics else ''))
                        
    total_traces = 0
    main_trace_indices = []
    
    # 1. Plot Main Panel (Strategy Equity)
    eq_data = results.strategy_equity
    if isinstance(eq_data, pd.Series):
        fig.add_trace(go.Scatter(x=eq_data.index, y=eq_data.values, name=eq_data.name or 'Equity', mode='lines', line=dict(width=1, color='#00E676')), row=1, col=1)
        main_trace_indices.append(total_traces)
        total_traces += 1
    elif isinstance(eq_data, pd.DataFrame):
        colors = {'Equity': '#00E676', 'Gross Equity': '#FF3D00', 'Benchmark': '#00B0FF'}
        for col in eq_data.columns:
            color = colors.get(col, None)
            line_kwargs = dict(width=1)
            if color:
                line_kwargs['color'] = color
            fig.add_trace(go.Scatter(x=eq_data.index, y=eq_data[col], name=col, mode='lines', line=line_kwargs), row=1, col=1)
            main_trace_indices.append(total_traces)
            total_traces += 1
            
    # 2. Plot Sub Panels
    sub_trace_groups = {}
    
    first_metric = True
    for name, data in valid_metrics.items():
        indices = []
        is_visible = first_metric
        
        if isinstance(data, pd.Series):
            fig.add_trace(go.Scatter(x=data.index, y=data.values, name=f"{name}", mode='lines', line=dict(width=1), visible=is_visible), row=2, col=1)
            indices.append(total_traces)
            total_traces += 1
        elif isinstance(data, pd.DataFrame):
            for col in data.columns:
                if name == 'Drawdown':
                    fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, mode='lines', fill='tozeroy', line=dict(width=1, color='#FF5252'), visible=is_visible), row=2, col=1)
                else:
                    fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, mode='lines', line=dict(width=1), visible=is_visible), row=2, col=1)
                
                indices.append(total_traces)
                total_traces += 1
                
        sub_trace_groups[name] = indices
        first_metric = False
        
    # 3. Create Updatemenus (Dropdown)
    buttons = []
    for name, indices in sub_trace_groups.items():
        vis_array = [False] * total_traces
        for idx in main_trace_indices:
            vis_array[idx] = True
        for idx in indices:
            vis_array[idx] = True
            
        button = dict(
            label=name,
            method="update",
            args=[{"visible": vis_array},
                  {"annotations[1].text": name}]
        )
        buttons.append(button)
        
    if buttons:
        fig.update_layout(
            updatemenus=[dict(
                active=0,
                buttons=buttons,
                x=0.0,
                xanchor="left",
                y=1.12,
                yanchor="bottom",
                direction="down",
                showactive=True
            )]
        )
        
    fig.update_layout(
        height=700,
        width=1200,
        template="plotly_dark",
        margin=dict(l=40, r=40, t=80, b=80),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12
        )
    )
    
    fig.show()

def plot_signals(df: pd.DataFrame, position_col='position', price_col='close'):
    """
    Plot the price chart with Buy/Sell markers based on the position column.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index if isinstance(df.index, pd.DatetimeIndex) else df['timestamp'],
        y=df[price_col],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=1)
    ))
    
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
    
    fig.update_layout(title="Trading Signals", template="plotly_dark")
    fig.show()
