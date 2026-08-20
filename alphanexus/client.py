import logging
import requests
from typing import Optional
from .exceptions import AuthenticationError, APIConnectionError

logger = logging.getLogger("alphanexus")

class Client:
    """Main client for interacting with the Alpha Nexus API."""
    
    def __init__(self, token: Optional[str] = None, base_url: str = "https://alpha-nexus.the20.sg"):
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def login(self, email: str, password: str):
        """Authenticate with email and password to obtain a session token."""
        logger.info(f"Authenticating with {self.base_url}...")
        try:
            resp = self.session.post(f"{self.base_url}/api/auth/login", json={
                "email": email,
                "password": password
            })
            
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("token")
                if token:
                    self.token = token
                    logger.info("Login successful! Alpha Nexus session initialized.")
                    return token
                else:
                    raise AuthenticationError("Login failed: 'token' missing from response.")
            else:
                raise AuthenticationError(f"Login failed: HTTP {resp.status_code} - {resp.text}")
        except requests.RequestException as e:
            raise APIConnectionError(f"Network error during login: {e}")

    def get_auth_headers(self) -> dict:
        if not self.token:
            raise AuthenticationError("No token available. Please call login() or initialize Client with a token.")
        return {"Authorization": f"Bearer {self.token}"}
