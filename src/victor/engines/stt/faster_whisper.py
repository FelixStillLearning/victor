"""Faster-Whisper CTranslate2 transcription engine."""

from typing import Any, Dict, Optional
import numpy as np
from victor.engines.stt.base import STTEngine


class FasterWhisperEngine(STTEngine):
    """Transcription engine utilizing Faster-Whisper and CTranslate2."""

    def __init__(self) -> None:
        self.model = None

    def initialize(self, config: Dict[str, Any]) -> bool:
        model_size = config.get("model_size", "small")
        device = config.get("device", "cpu")
        compute_type = config.get("compute_type", "int8")
        threads = config.get("threads", 8)

        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type, cpu_threads=threads)
            return True
        except Exception as err:
            print(f"Warning: Failed to load Faster-Whisper model: {err}")
            return False

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> str:
        if self.model is None:
            return ""
        try:
            segments, _ = self.model.transcribe(
                audio_data,
                language=language or "en",
                beam_size=1,
                initial_prompt="Hey Victor. Buka aplikasi, catat, putar lagu.",
            )
            return " ".join(s.text for s in segments).strip()
        except Exception:
            return ""
