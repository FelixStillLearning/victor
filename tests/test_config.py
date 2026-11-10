"""Unit tests for configuration management."""

import json
from pathlib import Path
from victor.core.config import ConfigManager


def test_config_defaults(tmp_path: Path) -> None:
    cfg_file = tmp_path / "test_config.toml"
    cfg_file.write_text("""
[user]
name = "Tester"
honorific = "sir"

[engines]
llm = "ollama"
    """)

    cfg = ConfigManager(explicit_path=cfg_file)
    assert cfg.get("user.name") == "Tester"
    assert cfg.get("user.honorific") == "sir"
    assert cfg.get("engines.llm") == "ollama"
    assert cfg.get("nonexistent.key", "default_val") == "default_val"


def test_legacy_migration() -> None:
    legacy = {
        "city": "Surabaya",
        "todoist_token": "secret_token_123",
        "thesis_dir": "/tmp/thesis",
    }
    migrated = ConfigManager._migrate_legacy_config(legacy)

    assert migrated["location"]["city"] == "Surabaya"
    assert migrated["plugins"]["tasks"]["todoist"]["api_token"] == "secret_token_123"
    assert migrated["plugins"]["notes"]["obsidian"]["vault_path"] == "/tmp/thesis"
    assert migrated["user"]["honorific"] == "sir"
