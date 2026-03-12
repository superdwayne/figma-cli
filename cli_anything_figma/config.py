"""Configuration management for cli-anything-figma."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "cli-anything-figma"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_TOKEN_KEY = "FIGMA_ACCESS_TOKEN"
ENV_TEAM_KEY = "FIGMA_TEAM_ID"


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file, with env var overrides."""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)

    # Environment variables take precedence
    if os.environ.get(ENV_TOKEN_KEY):
        config["access_token"] = os.environ[ENV_TOKEN_KEY]
    if os.environ.get(ENV_TEAM_KEY):
        config["team_id"] = os.environ[ENV_TEAM_KEY]

    return config


def save_config(config: dict):
    """Persist configuration to disk."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_token() -> str | None:
    """Retrieve the Figma access token."""
    return load_config().get("access_token")


def set_token(token: str):
    """Store the Figma access token."""
    config = load_config()
    config["access_token"] = token
    save_config(config)


def get_team_id() -> str | None:
    """Retrieve the default team ID."""
    return load_config().get("team_id")


def set_team_id(team_id: str):
    """Store the default team ID."""
    config = load_config()
    config["team_id"] = team_id
    save_config(config)
