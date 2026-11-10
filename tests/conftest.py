"""Pytest fixtures for V.I.C.T.O.R. test suite."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pytest

# Ensure src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from victor.core.config import ConfigManager
from victor.engines.llm.base import LLMEngine
from victor.plugins.base import VictorPlugin
from victor.plugins.registry import PluginRegistry


class MockLLMEngine(LLMEngine):
    """Mock LLM engine for testing fallback routing."""

    def __init__(self, predefined_response: str = "Mock response, sir.") -> None:
        self.predefined_response = predefined_response
        self.last_prompt: str = ""

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def query(self, prompt: str, system_prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        self.last_prompt = prompt
        return self.predefined_response


class DummyPlugin(VictorPlugin):
    """Simple plugin fixture for testing registration and dispatch."""

    name = "dummy"
    description = "Dummy test plugin"
    keywords = ["ping", "test"]

    def setup(self, config: Dict[str, Any]) -> bool:
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        if "ping" in intent:
            return "Pong, sir."
        return None


@pytest.fixture
def mock_llm() -> MockLLMEngine:
    return MockLLMEngine()


@pytest.fixture
def dummy_plugin() -> DummyPlugin:
    return DummyPlugin()


@pytest.fixture
def test_registry(dummy_plugin: DummyPlugin) -> PluginRegistry:
    reg = PluginRegistry()
    reg.register(dummy_plugin)
    return reg
