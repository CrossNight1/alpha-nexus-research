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

def get_token_session(email: str, password: str, base_url: str = "https://alpha-nexus.the20.sg"):
    """
    Login to Alpha Nexus using email and password to automatically obtain a session token.
    
    Args:
        email (str): Your Alpha Nexus account email/username.
        password (str): Your password.
        base_url (str, optional): The base URL of the Alpha Nexus API.
    """
    import requests
    set_base_url(base_url)
    
    print(f"Authenticating with {base_url}...")
    try:
        response = requests.post(f"{base_url}/api/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                set_token(token)
                print("Login successful! Alpha Nexus Research environment is initialized.")
                return token
            else:
                raise ValueError("Login failed: 'token' missing from response payload.")
        else:
            raise ValueError(f"Login failed: HTTP {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error during login: {e}")
        raise

# Expose sub-modules
from . import core
from . import data
from . import backtest
from . import visualize
from . import helper
