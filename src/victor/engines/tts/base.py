"""Text-to-Speech (TTS) engine base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class TTSEngine(ABC):
    """Abstract interface for speech synthesis engines."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Load synthesis model weights and setup audio output."""
        pass

    @abstractmethod
    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """Synthesize input text directly into a designated WAV output file."""
        pass
