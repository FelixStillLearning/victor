"""openWakeWord local detection engine implementation."""

from typing import Any, Dict
import numpy as np
from victor.engines.wakeword.base import WakeWordEngine


class OpenWakeWordEngine(WakeWordEngine):
    """Wake-word detection utilizing openWakeWord and ONNX Runtime."""

    def __init__(self) -> None:
        self.model = None
        self.target_model_name = "hey_jarvis"

    def initialize(self, config: Dict[str, Any]) -> bool:
        self.target_model_name = config.get("model", "hey_jarvis")
        try:
            from openwakeword.model import Model  # type: ignore
            self.model = Model(wakeword_models=[self.target_model_name], inference_framework="onnx")
            return True
        except Exception as err:
            print(f"Warning: Failed to load openWakeWord model: {err}")
            return False

    def predict(self, audio_chunk: np.ndarray) -> float:
        if self.model is None:
            return 0.0
        try:
            prediction = self.model.predict(audio_chunk)
            return float(prediction.get(self.target_model_name, 0.0))
        except Exception:
            return 0.0
