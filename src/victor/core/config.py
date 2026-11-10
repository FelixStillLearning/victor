"""Configuration loader and schema validator for V.I.C.T.O.R."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

DEFAULT_CONFIG_LOCATIONS = [
    Path.home() / ".config/victor/config.toml",
    Path("./config/config.toml"),
    Path(__file__).resolve().parent.parent.parent.parent / "config/config.example.toml",
]

LEGACY_CONFIG_LOCATION = Path.home() / ".config/jarvis/config.json"


class ConfigManager:
    """Manages application configuration, hierarchy, and value retrieval."""

    def __init__(self, explicit_path: Optional[Path] = None) -> None:
        self.config_path: Optional[Path] = None
        self._data: Dict[str, Any] = {}
        self.load(explicit_path)

    def load(self, explicit_path: Optional[Path] = None) -> None:
        """Load configuration from the first available location."""
        candidate_paths = [explicit_path] if explicit_path else DEFAULT_CONFIG_LOCATIONS

        for path in candidate_paths:
            if path and path.exists() and path.is_file():
                try:
                    with open(path, "rb") as f:
                        self._data = tomllib.load(f)
                        self.config_path = path
                        break
                except Exception as err:
                    print(f"Warning: Failed to parse configuration file at {path}: {err}")

        # Attempt legacy import fallback if no modern TOML config was resolved
        if not self._data and LEGACY_CONFIG_LOCATION.exists():
            try:
                with open(LEGACY_CONFIG_LOCATION, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                    self._data = self._migrate_legacy_config(legacy_data)
                    self.config_path = LEGACY_CONFIG_LOCATION
            except Exception as err:
                print(f"Warning: Failed to read legacy configuration: {err}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a nested configuration value using dot notation (e.g., 'engines.llm')."""
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def as_dict(self) -> Dict[str, Any]:
        """Return the raw configuration dictionary."""
        return self._data

    @staticmethod
    def _migrate_legacy_config(legacy: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy config.json into modern dictionary layout."""
        return {
            "user": {"name": "Felix", "honorific": "sir", "persona": "butler"},
            "location": {"city": legacy.get("city", "")},
            "engines": {
                "llm": "claude_cli",
                "stt": "faster_whisper",
                "tts": "piper",
                "wakeword": "openwakeword",
            },
            "plugins": {
                "enabled": ["hyprland", "media", "tasks", "notes", "phone"],
                "media": {
                    "spotify_client_id": legacy.get("spotify_client_id", ""),
                    "spotify_client_secret": legacy.get("spotify_client_secret", ""),
                },
                "tasks": {"todoist": {"api_token": legacy.get("todoist_token", "")}},
                "notes": {"obsidian": {"vault_path": legacy.get("thesis_dir", "")}},
            },
            "integrations": {
                "calendar_ics_url": legacy.get("calendar_ics_url", ""),
                "seminar_date": legacy.get("seminar_date", ""),
            },
        }


# Global singleton instance
_instance: Optional[ConfigManager] = None


def get_config(reload: bool = False) -> ConfigManager:
    """Retrieve the global ConfigManager singleton."""
    global _instance
    if _instance is None or reload:
        _instance = ConfigManager()
    return _instance
