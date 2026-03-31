from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(config_path: str = "config.yaml") -> dict:
    load_dotenv()

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. Copy config.example.yaml to config.yaml and fill in your settings."
        )

    with open(path) as f:
        config = yaml.safe_load(f)

    config["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]
    config["smtp_password"] = os.environ.get("SMTP_PASSWORD", "")
    config["semantic_scholar_api_key"] = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")

    db_path = config.get("storage", {}).get("db_path", "~/.paper-digest/papers.db")
    config.setdefault("storage", {})["db_path"] = os.path.expanduser(db_path)

    return config
