"""Piper neural text-to-speech engine implementation."""

import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, Optional

from victor.engines.tts.audio_effects import apply_audio_filter
from victor.engines.tts.base import TTSEngine


class PiperTTSEngine(TTSEngine):
    """Piper TTS synthesis with DSP filter enhancement."""

    def __init__(self) -> None:
        self.voice_model_path: Optional[Path] = None
        self.audio_filter: str = ""
        self._piper_voice: Any = None

    def initialize(self, config: Dict[str, Any]) -> bool:
        model_str = config.get("voice_model", "~/.local/share/piper/voices/jarvis-high.onnx")
        self.voice_model_path = Path(model_str).expanduser()
        self.audio_filter = config.get("audio_filter", "")

        if not self.voice_model_path.exists():
            return False

        try:
            from piper import PiperVoice  # type: ignore
            self._piper_voice = PiperVoice.load(str(self.voice_model_path))
            return True
        except Exception:
            return True  # Fallback to CLI piper invocation if python bindings absent

    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        if not self.voice_model_path or not self.voice_model_path.exists():
            return False

        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_wav = f"{tmp_dir}/raw.wav"

            if self._piper_voice is not None:
                try:
                    with wave.open(raw_wav, "wb") as w:
                        self._piper_voice.synthesize_wav(text, w)
                except Exception:
                    self._cli_synthesize(text, raw_wav)
            else:
                self._cli_synthesize(text, raw_wav)

            if self.audio_filter:
                return apply_audio_filter(raw_wav, output_path, self.audio_filter)
            else:
                import shutil
                shutil.copyfile(raw_wav, output_path)
                return True

    def _cli_synthesize(self, text: str, raw_wav: str) -> None:
        """Fallback synthesis using piper binary."""
        piper_bin = Path.home() / ".local/share/piper/venv/bin/piper"
        cmd = [str(piper_bin) if piper_bin.exists() else "piper", "-m", str(self.voice_model_path), "-f", raw_wav]
        subprocess.run(cmd, input=text.encode(), check=True, stderr=subprocess.DEVNULL)
