"""Speech-to-Text (STT) engine base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

try:
    import numpy as np  # type: ignore
except ImportError:
    np = None  # type: ignore


class STTEngine(ABC):
    """Abstract interface for acoustic transcription engines."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Load transcription model weights and setup compute backend."""
        pass

    @abstractmethod
    def transcribe(self, audio_data: Any, language: Optional[str] = None) -> str:
        """Transcribe floating-point or integer PCM audio buffer into text."""
        pass
