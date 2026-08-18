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
        self.strategy_equity = charts.get('Strategy Equity', {}).get('series', [])
        self.drawdown = charts.get('Drawdown', {}).get('series', [])
        self.portfolio_turnover = charts.get('Portfolio Turnover', {}).get('series', [])
        self.rolling_sharpe = charts.get('Rolling Sharpe', {}).get('series', [])
        self.rolling_beta = charts.get('Rolling Beta', {}).get('series', [])
        self.exposure = charts.get('Exposure', {}).get('series', [])
        self.trading_fees = charts.get('Trading Fees', {}).get('series', [])
        self.daily_weights = charts.get('Daily Weights', {}).get('series', [])

    def _repr_html_(self):
        """Allows Jupyter/Colab to natively render this object as an HTML table."""
        if not self.stats:
            return '<b>No statistics generated.</b>'
            
        filtered_stats = {k: v for k, v in self.stats.items() if k not in self.drop_keys}
        df = pd.DataFrame(list(filtered_stats.items()), columns=['Metric', 'Value'])
        
        top_rows = pd.DataFrame([
            {'Metric': 'Final Equity', 'Value': self.final_value}, 
            {'Metric': 'Total ROI (%)', 'Value': self.roi}
        ])
        
        return pd.concat([top_rows, df], ignore_index=True).set_index('Metric').to_html()

    def __repr__(self):
        return "<VectorizedResult: Call .summary() for statistics, or access time-series properties like .strategy_equity>"

    def summary(self):
        """Displays the summary table in notebooks without returning the object."""
        from IPython.display import display, HTML
        display(HTML(self._repr_html_()))
