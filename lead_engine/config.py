"""Configuration loader for the lead qualification engine."""

import yaml
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load and validate a YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _validate_config(config)
    return config


def _validate_config(config: dict):
    """Basic validation of required config sections."""
    required_sections = ["input", "output", "size_scoring", "industry_tiers", "keyword_signals", "tiers"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: '{section}'")

    if "brackets" not in config["size_scoring"]:
        raise ValueError("size_scoring must contain 'brackets'")

    if "categories" not in config["keyword_signals"]:
        raise ValueError("keyword_signals must contain 'categories'")
