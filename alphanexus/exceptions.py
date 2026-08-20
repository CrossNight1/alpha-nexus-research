class AlphaNexusError(Exception):
    """Base class for all Alpha Nexus SDK exceptions."""
    pass

class AuthenticationError(AlphaNexusError):
    """Raised when authentication fails (401/403)."""
    pass

class APIConnectionError(AlphaNexusError):
    """Raised when there's a network issue connecting to the API."""
    pass

class BacktestTimeoutError(AlphaNexusError):
    """Raised when a backtest runs longer than the allowed timeout."""
    pass
