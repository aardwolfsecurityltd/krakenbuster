"""Configuration file handling for KrakenBuster."""

from __future__ import annotations

import configparser
from pathlib import Path


CONFIG_PATH = Path.home() / ".krakenbuster.conf"

DEFAULTS = {
    "general": {
        "threads": "50",
        "rate_limit": "200",
        "proxy": "",
        "output_directory": "./output",
    },
    "wordlists": {
        "last_used": "",
    },
    "tools": {
        "last_dir_tool": "feroxbuster",
        "last_vhost_tool": "ffuf",
        "last_dns_tool": "gobuster",
    },
}


def load_config() -> configparser.ConfigParser:
    """Load configuration from ~/.krakenbuster.conf, creating defaults if needed."""
    config = configparser.ConfigParser()

    for section, values in DEFAULTS.items():
        config[section] = values

    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    else:
        save_config(config)
        print(f"Created default configuration at {CONFIG_PATH}")

    return config


def save_config(config: configparser.ConfigParser) -> None:
    """Write configuration to ~/.krakenbuster.conf."""
    with open(CONFIG_PATH, "w") as fh:
        config.write(fh)


def update_config(section: str, key: str, value: str) -> None:
    """Update a single configuration value and save."""
    config = load_config()
    if section not in config:
        config[section] = {}
    config[section][key] = value
    save_config(config)
