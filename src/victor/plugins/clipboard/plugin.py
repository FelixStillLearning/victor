"""Clipboard processing plugin implementation."""

import re
import subprocess
from typing import Any, Dict, Optional

from victor.plugins.base import VictorPlugin


class ClipboardPlugin(VictorPlugin):
    """Processes, reformats, and reads text from Wayland clipboard."""

    name = "clipboard"
    description = "Wayland clipboard text manipulations"
    keywords = ["clipboard", "papan klip", "format clipboard", "baca clipboard"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        # Read clipboard
        if re.search(r"\b(read|baca|what is on (the|my))\b.*\b(clipboard|papan klip)\b", t):
            text = self._get_clipboard_text()
            if not text:
                return "The clipboard is currently empty, sir."
            words = text.split()
            count = len(words)
            preview = " ".join(words[:15])
            return f"The clipboard contains {count} words. It begins with: {preview}."

        # Clear clipboard
        if re.search(r"\b(clear|hapus|kosongkan)\b.*\b(clipboard|papan klip)\b", t):
            self._set_clipboard_text("")
            return "The clipboard has been cleared, sir."

        # Reformat clipboard as clean single line
        if re.search(r"\b(clean|format|rapikan)\b.*\b(clipboard|papan klip)\b", t):
            text = self._get_clipboard_text()
            if not text:
                return "The clipboard is empty, sir."
            cleaned = " ".join(text.split())
            self._set_clipboard_text(cleaned)
            return "The clipboard text has been formatted into a single clean line, sir."

        return None

    def _get_clipboard_text(self) -> str:
        """Fetch current text from Wayland clipboard via wl-paste."""
        try:
            return subprocess.run(["wl-paste", "--no-newline"],
                                  capture_output=True, text=True, timeout=2).stdout.strip()
        except Exception:
            return ""

    def _set_clipboard_text(self, text: str) -> None:
        """Inject text into Wayland clipboard via wl-copy."""
        try:
            subprocess.run(["wl-copy"], input=text.encode(), capture_output=True, timeout=2)
        except Exception:
            pass
