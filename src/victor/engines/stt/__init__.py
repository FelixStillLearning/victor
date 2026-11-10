"""Speech-to-text engines package."""

from victor.engines.stt.base import STTEngine
from victor.engines.stt.faster_whisper import FasterWhisperEngine

__all__ = ["STTEngine", "FasterWhisperEngine"]
