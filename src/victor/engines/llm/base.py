"""Language model reasoning engine base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class LLMEngine(ABC):
    """Abstract interface for language reasoning and intent fallback engines."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize connection, endpoint, or local process parameters."""
        pass

    @abstractmethod
    def query(self, prompt: str, system_prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        """Submit prompt and return model response string."""
        pass
