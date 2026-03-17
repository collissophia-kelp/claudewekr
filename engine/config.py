"""Configuration loading and management for Kelp Target Engine."""

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"
DEFAULT_SCORING_GUIDE_PATH = Path(__file__).parent.parent / "data" / "scoring_guide.json"


def load_config(path: Path | None = None) -> dict:
    """Load configuration from JSON file."""
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return json.load(f)


def save_config(config: dict, path: Path | None = None) -> None:
    """Save configuration to JSON file."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def load_scoring_guide(path: Path | None = None) -> dict:
    """Load scoring guide from JSON file."""
    guide_path = path or DEFAULT_SCORING_GUIDE_PATH
    if not guide_path.exists():
        raise FileNotFoundError(f"Scoring guide not found: {guide_path}")
    with open(guide_path, "r") as f:
        return json.load(f)


def get_weights(config: dict) -> dict[str, float]:
    """Extract scoring weights from config."""
    return config["scoring_weights"]


def get_thresholds(config: dict) -> dict[str, float]:
    """Extract tier thresholds from config."""
    return config["tier_thresholds"]


def get_revenue_assumptions(config: dict) -> dict[str, Any]:
    """Extract revenue assumptions from config."""
    return config["revenue_assumptions"]


def update_config_value(config: dict, section: str, key: str, value: Any) -> dict:
    """Update a specific config value and return the updated config."""
    if section not in config:
        raise KeyError(f"Unknown config section: {section}")
    if key not in config[section]:
        raise KeyError(f"Unknown key '{key}' in section '{section}'")
    config[section][key] = value
    return config
