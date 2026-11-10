"""Unit tests for plugin lifecycle and bundled plugins."""

from victor.plugins.clipboard import ClipboardPlugin
from victor.plugins.history import HistoryPlugin
from victor.plugins.hyprland import HyprlandPlugin
from victor.plugins.media import MediaPlugin
from victor.plugins.notes import NotesPlugin
from victor.plugins.phone import PhonePlugin
from victor.plugins.registry import PluginRegistry
from victor.plugins.tasks import TasksPlugin
from victor.plugins.vision import VisionPlugin


def test_registry_registration() -> None:
    reg = PluginRegistry()
    p = HyprlandPlugin()
    assert reg.register(p, {"enable_dynamic_island": False}) is True
    assert "hyprland" in reg.plugins
    assert p.enabled is True

    reg.unregister("hyprland")
    assert "hyprland" not in reg.plugins


def test_hyprland_plugin_workspace() -> None:
    p = HyprlandPlugin()
    p.setup({})
    res = p.handle("pindah ke workspace 3", {})
    assert res == "Workspace 3, sir."

    res_en = p.handle("workspace five", {})
    assert res_en == "Workspace 5, sir."


def test_media_plugin_playback() -> None:
    p = MediaPlugin()
    p.setup({})
    res = p.handle("pause lagu", {})
    assert res == "Paused, sir."

    res_next = p.handle("next track", {})
    assert res_next == "Next track, sir."


def test_notes_plugin() -> None:
    p = NotesPlugin()
    p.setup({})
    res = p.handle("catat revisi bab dua", {})
    assert res == "Noted, sir."


def test_tasks_plugin_unconfigured() -> None:
    p = TasksPlugin()
    p.setup({})
    res = p.handle("tambah tugas selesaikan laporan besok", {})
    assert "Todoist token is not configured" in res


def test_phone_plugin() -> None:
    p = PhonePlugin()
    p.setup({})
    # If no phone connected, reports unreachable
    res = p.handle("cari hp saya", {})
    assert "cannot reach your phone" in res or "Ringing your phone" in res


def test_vision_plugin() -> None:
    p = VisionPlugin()
    p.setup({})
    res = p.handle("baca layar", {})
    assert res is not None
    assert "sir" in res


def test_history_plugin() -> None:
    p = HistoryPlugin()
    p.setup({})
    # Record a command
    p.handle("test intent", {"response": "test response"})
    # Recall inquiry
    recall = p.handle("tadi aku tanya apa?", {})
    assert recall is not None
