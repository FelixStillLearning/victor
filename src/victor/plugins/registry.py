"""Plugin discovery, lifecycle management, and execution dispatcher."""

import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from victor.plugins.base import VictorPlugin

logger = logging.getLogger("victor.plugins")


class PluginRegistry:
    """Manages loaded plugins and dispatches intent requests."""

    def __init__(self) -> None:
        self.plugins: Dict[str, VictorPlugin] = {}

    def register(self, plugin: VictorPlugin, config: Optional[Dict[str, Any]] = None) -> bool:
        """Register and initialize a plugin instance."""
        plugin_name = plugin.name
        cfg = config or {}
        try:
            success = plugin.setup(cfg)
            if success:
                plugin.enabled = True
                self.plugins[plugin_name] = plugin
                return True
            else:
                logger.warning(f"Plugin '{plugin_name}' setup returned False. Not enabled.")
                return False
        except Exception as err:
            logger.error(f"Error initializing plugin '{plugin_name}': {err}")
            return False

    def unregister(self, plugin_name: str) -> None:
        """Unregister and teardown a loaded plugin."""
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].teardown()
            except Exception as err:
                logger.error(f"Error during teardown for plugin '{plugin_name}': {err}")
            del self.plugins[plugin_name]

    def dispatch(self, intent: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Pass intent through enabled plugins until one returns a spoken response.
        Returns the spoken response string, or None if no plugin handled it.
        """
        ctx = context or {}
        for name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
            try:
                response = plugin.handle(intent, ctx)
                if response is not None:
                    return response
            except Exception as err:
                logger.error(f"Unhandled exception in plugin '{name}' during dispatch: {err}")
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata summary for all registered plugins."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "keywords": p.keywords,
                "enabled": p.enabled,
            }
            for p in self.plugins.values()
        ]


# Global plugin registry singleton
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Retrieve the global PluginRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
