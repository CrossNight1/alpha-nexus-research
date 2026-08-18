import pandas as pd

class VectorizedResult:
    """
    A rich object representing the results of a vectorized backtest.
    Provides easy access to performance statistics and time-series arrays for charting.
    """
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.metrics = raw_data.get('metrics', {})
        self.stats = self.metrics.get('statistics', {})
        
        self.final_value = self.metrics.get('final_value')
        self.roi = self.metrics.get('roi')
        
        # Keys to exclude from the summary DataFrame
        self.drop_keys = {
            'Tracking Error',
            'Treynor Ratio',
            'Estimated Strategy Capacity',
            'Lowest Capacity Asset',
            'Fitness',
            'Avg Total Cost',
            'Avg Slippage Cost',
            'Avg Fee'
        }
        
        # Time-series charts for easy plotting
        charts = self.metrics.get('charts', {})
        self.strategy_equity = self._to_dataframe(charts.get('Strategy Equity', {}).get('series', {}))
        self.drawdown = self._to_dataframe(charts.get('Drawdown', {}).get('series', {}))
        self.portfolio_turnover = self._to_dataframe(charts.get('Portfolio Turnover', {}).get('series', {}))
        self.rolling_sharpe = self._to_dataframe(charts.get('Rolling Sharpe', {}).get('series', {}))
        self.rolling_beta = self._to_dataframe(charts.get('Rolling Beta', {}).get('series', {}))
        self.exposure = self._to_dataframe(charts.get('Exposure', {}).get('series', {}))
        self.trading_fees = self._to_dataframe(charts.get('Trading Fees', {}).get('series', {}))
        self.daily_weights = self._to_dataframe(charts.get('Daily Weights', {}).get('series', {}))

    def _to_dataframe(self, chart_series):
        if not chart_series or not isinstance(chart_series, dict):
            return chart_series
            
        try:
            series_list = []
            for series_name, series_data in chart_series.items():
                vals = series_data.get('values', {})
                if isinstance(vals, dict) and 't' in vals and 'v' in vals:
                    df = pd.DataFrame({'timestamp': vals['t'], series_name: vals['v']})
                elif isinstance(vals, list) and len(vals) > 0 and isinstance(vals[0], dict):
                    df = pd.DataFrame([{'timestamp': d.get('x'), series_name: d.get('y')} for d in vals])
                elif isinstance(vals, list) and len(vals) > 0 and isinstance(vals[0], list):
                    df = pd.DataFrame(vals, columns=['timestamp', series_name])
                else:
                    continue
                    
                if not df.empty:
                    if df['timestamp'].iloc[0] > 1e11:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    else:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                    series_list.append(df.set_index('timestamp'))
                    
            if not series_list:
                return chart_series
                
            combined_df = pd.concat(series_list, axis=1)
            # If there's only 1 series, return as a Pandas Series
            if len(combined_df.columns) == 1:
                return combined_df.iloc[:, 0]
            return combined_df
        except Exception:
            return chart_series

    def __repr__(self):
        attrs = [
            'final_value', 'roi', 'strategy_equity', 'drawdown', 
            'portfolio_turnover', 'rolling_sharpe', 'rolling_beta', 
            'exposure', 'trading_fees', 'daily_weights'
        ]
        return f"<VectorizedResult Object>\nAvailable attributes:\n  - " + "\n  - ".join(attrs) + "\n\nTip: Call results.summary() to view the statistics table."

    def summary(self):
        """Displays the summary table in notebooks without returning the object."""
        if not self.stats:
            print('No statistics generated.')
            return
            
        filtered_stats = {k: v for k, v in self.stats.items() if k not in self.drop_keys}
        df = pd.DataFrame(list(filtered_stats.items()), columns=['Metric', 'Value'])
        
        top_rows = pd.DataFrame([
            {'Metric': 'Final Equity', 'Value': self.final_value}, 
            {'Metric': 'Total ROI (%)', 'Value': self.roi}
        ])
        
        html_table = pd.concat([top_rows, df], ignore_index=True).set_index('Metric').to_html()
        
        from IPython.display import display, HTML
        display(HTML(html_table))
