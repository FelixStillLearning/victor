"""Linux AT-SPI accessibility tree parser for semantic UI reading."""

import json
import subprocess
from typing import Dict, List, Optional


class AtspiReader:
    """Interrogates active window accessibility tree or compositor metadata."""

    def __init__(self) -> None:
        self.pyatspi_available = False
        try:
            import pyatspi  # type: ignore
            self.pyatspi = pyatspi
            self.pyatspi_available = True
        except ImportError:
            pass

    def get_active_window_context(self) -> Dict[str, str]:
        """Extract focused application class, title, and accessible text content."""
        metadata = self._get_hyprland_active_window()
        accessible_text = ""

        if self.pyatspi_available:
            accessible_text = self._query_atspi_active_text()

        return {
            "title": metadata.get("title", "Unknown Window"),
            "class": metadata.get("class", "Unknown Class"),
            "pid": str(metadata.get("pid", 0)),
            "content": accessible_text,
        }

    def _get_hyprland_active_window(self) -> Dict[str, str]:
        """Fetch active window details from Hyprland compositor."""
        try:
            out = subprocess.run(["hyprctl", "activewindow", "-j"],
                                 capture_output=True, text=True, timeout=3).stdout
            return json.loads(out or "{}")
        except Exception:
            return {}

    def _query_atspi_active_text(self) -> str:
        """Traverse accessibility tree to collect text from focused element hierarchy."""
        collected: List[str] = []
        try:
            reg = self.pyatspi.Registry
            desktop = reg.getDesktop(0)
            for app in desktop:
                for window in app:
                    if window.getState().contains(self.pyatspi.STATE_ACTIVE):
                        self._walk_accessible_node(window, collected, depth=0)
                        break
        except Exception:
            pass
        return " ".join(collected)[:2000]

    def _walk_accessible_node(self, node: Any, buffer: List[str], depth: int = 0) -> None:
        """Recursive node traversal extracting text components."""
        if depth > 5 or len(buffer) > 50:
            return
        try:
            name = node.name.strip()
            if name and name not in buffer:
                buffer.append(name)
            # Query text interface
            text_iface = node.queryText()
            txt = text_iface.getText(0, text_iface.characterCount).strip()
            if txt and txt not in buffer:
                buffer.append(txt)
        except Exception:
            pass

        try:
            for i in range(node.childCount):
                self._walk_accessible_node(node.getChildAtIndex(i), buffer, depth + 1)
        except Exception:
            pass
