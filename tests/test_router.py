"""Unit tests for the IntentRouter."""

from victor.core.router import IntentRouter
from victor.plugins.registry import PluginRegistry


def test_router_ping(test_registry: PluginRegistry, mock_llm) -> None:
    router = IntentRouter(registry=test_registry, llm=mock_llm)
    res = router.route("Victor, ping")
    assert res == "Pong, sir."


def test_router_wake_prefix_stripping(test_registry: PluginRegistry) -> None:
    router = IntentRouter(registry=test_registry)
    res = router.route("Hey Victor, what time is it?")
    assert "It is" in res
    assert "sir" in res


def test_router_empty_input(test_registry: PluginRegistry) -> None:
    router = IntentRouter(registry=test_registry)
    res = router.route("Hey Victor")
    assert res == "Yes, sir?"


def test_router_cancellation(test_registry: PluginRegistry) -> None:
    router = IntentRouter(registry=test_registry)
    res = router.route("Victor, never mind")
    assert res == "Very well, sir."


def test_router_destructive_confirmation(test_registry: PluginRegistry) -> None:
    router = IntentRouter(registry=test_registry)
    # Trigger shutdown confirmation
    prompt = router.route("Victor, shut down the laptop")
    assert "Shall I shut down the workstation, sir?" in prompt
    assert router.pending_confirmation is not None

    # Cancel confirmation
    cancel_res = router.route("No, cancel that")
    assert cancel_res == "Very well, sir. Action cancelled."
    assert router.pending_confirmation is None


def test_router_llm_fallback(mock_llm) -> None:
    empty_reg = PluginRegistry()
    mock_llm.predefined_response = "The capital of France is Paris, sir."
    router = IntentRouter(registry=empty_reg, llm=mock_llm)

    res = router.route("Victor, tell me the capital of France")
    assert res == "The capital of France is Paris, sir."
