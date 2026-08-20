import logging
from .client import Client
from .exceptions import AlphaNexusError, AuthenticationError, APIConnectionError, BacktestTimeoutError
from .models import AssetData, PositionTarget, VectorizedResult

# Global default client instance for ease of use
_default_client = Client()

def login(email: str, password: str, base_url: str = "https://alpha-nexus.the20.sg"):
    """Convenience method to login using the default global client."""
    _default_client.base_url = base_url.rstrip('/')
    return _default_client.login(email, password)

def init(token: str, base_url: str = "https://alpha-nexus.the20.sg"):
    """Convenience method to initialize the default global client with a session token."""
    _default_client.base_url = base_url.rstrip('/')
    _default_client.token = token
    return _default_client.verify()

def get_default_client() -> Client:
    """Returns the globally initialized Client instance."""
    return _default_client

# Set up null handler to avoid 'No handler found' warnings
logging.getLogger("alphanexus").addHandler(logging.NullHandler())

__all__ = [
    "Client",
    "login",
    "init",
    "get_default_client",
    "AssetData",
    "PositionTarget",
    "VectorizedResult",
    "AlphaNexusError",
    "AuthenticationError",
    "APIConnectionError",
    "BacktestTimeoutError"
]
