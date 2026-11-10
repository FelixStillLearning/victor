"""Abstract Base Class for V.I.C.T.O.R. plugins."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VictorPlugin(ABC):
    """Abstract base class that all Victor extensions must implement."""

    name: str = ""
    description: str = ""
    keywords: List[str] = []

    def __init__(self) -> None:
        self.enabled: bool = False
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration parameters.
        Returns True if setup succeeded and plugin is ready to handle commands.
        """
        pass

    @abstractmethod
    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Process the user intent.
        Returns a string response to be spoken by Victor if handled,
        or None if the intent should fall through to subsequent handlers.
        """
        pass

    def teardown(self) -> None:
        """Release system resources, sockets, or background threads."""
        pass
