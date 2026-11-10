"""Local Ollama REST API reasoning adapter."""

import json
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from victor.engines.llm.base import LLMEngine


class OllamaEngine(LLMEngine):
    """Executes reasoning queries against a local Ollama HTTP server."""

    def __init__(self) -> None:
        self.host: str = "http://localhost:11434"
        self.model: str = "qwen2.5:3b"
        self.timeout: int = 30

    def initialize(self, config: Dict[str, Any]) -> bool:
        self.host = config.get("host", "http://localhost:11434").rstrip("/")
        self.model = config.get("model", "qwen2.5:3b")
        self.timeout = config.get("timeout_seconds", 30)
        return True

    def query(self, prompt: str, system_prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 128},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception:
            return ""
