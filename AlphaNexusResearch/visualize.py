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
            valid_metrics[name] = data
            
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        row_heights=[0.7, 0.3], vertical_spacing=0.05,
                        subplot_titles=('Strategy Equity', list(valid_metrics.keys())[0] if valid_metrics else ''))
                        
    total_traces = 0
    main_trace_indices = []
    
    # 1. Plot Main Panel (Strategy Equity)
    eq_data = results.strategy_equity
    if isinstance(eq_data, pd.Series):
        fig.add_trace(go.Scatter(x=eq_data.index, y=eq_data.values, name=eq_data.name or 'Equity', mode='lines'), row=1, col=1)
        main_trace_indices.append(total_traces)
        total_traces += 1
    elif isinstance(eq_data, pd.DataFrame):
        for col in eq_data.columns:
            fig.add_trace(go.Scatter(x=eq_data.index, y=eq_data[col], name=col, mode='lines'), row=1, col=1)
            main_trace_indices.append(total_traces)
            total_traces += 1
            
    # 2. Plot Sub Panels
    sub_trace_groups = {} # maps metric_name -> list of trace indices
    
    first_metric = True
    for name, data in valid_metrics.items():
        indices = []
        is_visible = first_metric
        
        if isinstance(data, pd.Series):
            fig.add_trace(go.Scatter(x=data.index, y=data.values, name=f"{name}", mode='lines', visible=is_visible), row=2, col=1)
            indices.append(total_traces)
            total_traces += 1
        elif isinstance(data, pd.DataFrame):
            for col in data.columns:
                # Use bar chart for weights/turnover/fees, otherwise lines
                mode = 'lines'
                plot_type = go.Scatter
                if name in ['Daily Weights', 'Portfolio Turnover', 'Trading Fees']:
                    # Plotly doesn't natively support stacking in Scatter without fill, but we can just use Lines for simplicity or Bar
                    fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, mode='lines', stackgroup='one' if name == 'Daily Weights' else None, visible=is_visible), row=2, col=1)
                else:
                    if name == 'Drawdown':
                        fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, mode='lines', fill='tozeroy', visible=is_visible), row=2, col=1)
                    else:
                        fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, mode='lines', visible=is_visible), row=2, col=1)
                
                indices.append(total_traces)
                total_traces += 1
                
        sub_trace_groups[name] = indices
        first_metric = False
        
    # 3. Create Updatemenus (Dropdown)
    buttons = []
    for name, indices in sub_trace_groups.items():
        # Visibility array: Main traces always True, this sub-group True, rest False
        vis_array = [False] * total_traces
        for idx in main_trace_indices:
            vis_array[idx] = True
        for idx in indices:
            vis_array[idx] = True
            
        button = dict(
            label=name,
            method="update",
            args=[{"visible": vis_array},
                  {"annotations[1].text": name}] # Update the subtitle
        )
        buttons.append(button)
        
    if buttons:
        fig.update_layout(
            updatemenus=[dict(
                active=0,
                buttons=buttons,
                x=0.0,
                xanchor="left",
                y=0.4,
                yanchor="bottom",
                direction="down",
                showactive=True
            )]
        )
        
    fig.update_layout(
        height=700, 
        template="plotly_dark",
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.show()
    
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
