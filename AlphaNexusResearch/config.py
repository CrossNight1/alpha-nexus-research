_state = {
    "token": None,
    "base_url": "https://alpha-nexus.the20.sg"
}

def set_token(token: str):
    _state["token"] = token

def get_token() -> str:
    token = _state["token"]
    if not token:
        raise ValueError("Token not set. Please call AlphaNexusResearch.init(token='YOUR_TOKEN') first.")
    return token

def set_base_url(url: str):
    _state["base_url"] = url.rstrip('/')

def get_base_url() -> str:
    return _state["base_url"]
