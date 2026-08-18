import os
from .config import set_token, set_base_url

def init(token: str, base_url: str = "https://alpha-nexus.the20.sg"):
    """
    Initialize the Alpha Nexus Research environment with your session token.
    
    Args:
        token (str): The session token provided by the Alpha Nexus UI.
        base_url (str, optional): The base URL of the Alpha Nexus API.
    """
    set_token(token)
    set_base_url(base_url)
    print(f"Alpha Nexus Research initialized successfully. Target: {base_url}")

# Expose sub-modules
from . import data
from . import backtest
from . import plot
from . import helper
