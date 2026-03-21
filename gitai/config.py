import tomllib
import tomli_w
from pathlib import Path

CONFIG_PATH = Path.home() / ".gitai.toml"

DEFAULT_CONFIG = {
    "model": "llama3.2",
    "provider": "ollama",
    "ollama_url": "http://localhost:11434",
    "commit_style": "conventional",
    "emoji": False,
}

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    with open(CONFIG_PATH, "rb") as f:
        user_config = tomllib.load(f)

    return {**DEFAULT_CONFIG, **user_config}

def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "wb") as f:
        tomli_w.dump(config, f)