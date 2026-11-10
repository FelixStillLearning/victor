"""Automated standalone test runner for V.I.C.T.O.R."""

import sys
import unittest
from pathlib import Path

# Ensure src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from victor.core.config import ConfigManager
from victor.core.router import IntentRouter
from victor.plugins.clipboard import ClipboardPlugin
from victor.plugins.history import HistoryPlugin
from victor.plugins.hyprland import HyprlandPlugin
from victor.plugins.media import MediaPlugin
from victor.plugins.notes import NotesPlugin
from victor.plugins.phone import PhonePlugin
from victor.plugins.registry import PluginRegistry
from victor.plugins.tasks import TasksPlugin
from victor.plugins.vision import VisionPlugin


class TestVictorCore(unittest.TestCase):
    """Test suite for core components."""

    def test_legacy_migration(self):
        legacy = {"city": "Bandung", "todoist_token": "token_abc", "thesis_dir": "/tmp/thesis"}
        migrated = ConfigManager._migrate_legacy_config(legacy)
        self.assertEqual(migrated["location"]["city"], "Bandung")
        self.assertEqual(migrated["plugins"]["tasks"]["todoist"]["api_token"], "token_abc")
        self.assertEqual(migrated["user"]["honorific"], "sir")

    def test_router_empty_and_cancel(self):
        reg = PluginRegistry()
        router = IntentRouter(registry=reg)
        self.assertEqual(router.route("Hey Victor"), "Yes, sir?")
        self.assertEqual(router.route("Victor, never mind"), "Very well, sir.")

    def test_router_destructive_flow(self):
        reg = PluginRegistry()
        router = IntentRouter(registry=reg)
        res = router.route("Victor, restart the laptop")
        self.assertIn("Shall I restart the workstation, sir?", res)
        self.assertIsNotNone(router.pending_confirmation)

        cancel_res = router.route("No, cancel that")
        self.assertEqual(cancel_res, "Very well, sir. Action cancelled.")
        self.assertIsNone(router.pending_confirmation)


class TestVictorPlugins(unittest.TestCase):
    """Test suite for bundled plugins."""

    def test_plugin_registration(self):
        reg = PluginRegistry()
        p = HyprlandPlugin()
        self.assertTrue(reg.register(p, {}))
        self.assertIn("hyprland", reg.plugins)
        self.assertTrue(p.enabled)

    def test_hyprland_workspace(self):
        p = HyprlandPlugin()
        p.setup({})
        self.assertEqual(p.handle("pindah ke workspace 4", {}), "Workspace 4, sir.")
        self.assertEqual(p.handle("workspace two", {}), "Workspace 2, sir.")

    def test_media_playback(self):
        p = MediaPlugin()
        p.setup({})
        self.assertEqual(p.handle("pause", {}), "Paused, sir.")
        self.assertEqual(p.handle("next track", {}), "Next track, sir.")
        self.assertEqual(p.handle("volume up", {}), "Volume up, sir.")

    def test_notes_plugin(self):
        p = NotesPlugin()
        p.setup({})
        self.assertEqual(p.handle("catat uji coba sistem", {}), "Noted, sir.")

    def test_tasks_plugin(self):
        p = TasksPlugin()
        p.setup({})
        res = p.handle("tambah tugas revisi bab dua besok", {})
        self.assertIn("Todoist token is not configured", res)

    def test_vision_plugin(self):
        p = VisionPlugin()
        p.setup({})
        res = p.handle("baca layar", {})
        self.assertIsNotNone(res)
        self.assertIn("sir", res)

    def test_history_plugin(self):
        p = HistoryPlugin()
        p.setup({})
        p.handle("test intent", {"response": "test response"})
        res = p.handle("tadi aku tanya apa?", {})
        self.assertIsNotNone(res)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVictorCore)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVictorPlugins))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
