"""Wake-word detection engine base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict

try:
    import numpy as np  # type: ignore
except ImportError:
    np = None  # type: ignore


class WakeWordEngine(ABC):
    """Abstract interface for local acoustic wake word models."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Load acoustic detection checkpoint."""
        pass

    @abstractmethod
    def predict(self, audio_chunk: Any) -> float:
        """Process 16kHz PCM audio chunk and return confidence score between 0.0 and 1.0."""
        pass
