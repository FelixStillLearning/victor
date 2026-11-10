"""Hyprland compositor plugin implementation."""

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from victor.core.persona import NUMBERS_MAP
from victor.plugins.base import VictorPlugin

APPS_MAP: Dict[str, list] = {
    r"discord|di ?skor|diskor|disc ord": ["caelestia", "toggle", "communication"],
    r"spotify|music|musik|lagu": ["caelestia", "toggle", "music"],
    r"browser|zen|internet": ["zen-browser"],
    r"vs ?code|visual studio|code|editor": ["code"],
    r"obsidian|notes?|catatan": ["obsidian"],
    r"terminal": ["foot"],
    r"files?|file manager|folder": ["thunar"],
    r"calculator|kalkulator": ["gnome-calculator"],
}

SITES_MAP: Dict[str, str] = {
    r"youtube|yutub": "https://youtube.com",
    r"gmail|email|e-mail": "https://mail.google.com",
    r"github": "https://github.com",
    r"whatsapp|wa": "https://web.whatsapp.com",
    r"scholar|google scholar": "https://scholar.google.com",
    r"drive|google drive": "https://drive.google.com",
    r"google": "https://google.com",
    r"claude": "https://claude.ai",
    r"chat ?gpt": "https://chatgpt.com",
    r"instagram|ig": "https://instagram.com",
}


class HyprlandPlugin(VictorPlugin):
    """Integrates window management, workspaces, and UI state with Hyprland."""

    name = "hyprland"
    description = "Hyprland workspace and window control"
    keywords = ["workspace", "close", "tutup", "open", "buka", "screenshot", "wallpaper", "lock"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.dynamic_island = config.get("enable_dynamic_island", True)
        self.island_name = config.get("dynamic_island_component", "jarvis-island")
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        # Workspace switching: "pindah ke workspace 3", "workspace two"
        words_pattern = "|".join(sorted(map(re.escape, NUMBERS_MAP.keys()), key=len, reverse=True))
        m = re.search(rf"\b(?:workspace|work space|ruang kerja|desktop)\s+(?:nomor\s+|number\s+)?(\d+|{words_pattern})\b", t)
        if m:
            val = m.group(1)
            n = int(val) if val.isdigit() else NUMBERS_MAP.get(val, 1)
            self._hypr_dispatch(f"workspace {n}")
            return f"Workspace {n}, sir."

        # Close application or window
        m = re.match(r"(?:tolong |please )?(?:tutup|close|quit|keluar dari)\b\s+(?:aplikasi\s+|app\s+|the\s+)?(.+)", t)
        if m:
            target = m.group(1).strip()
            if re.fullmatch(r"(jendela|window|this window|jendela ini|ini|this)", target):
                self._hypr_dispatch("killactive")
                return "Closed, sir."
            closed = self._close_named_app(target)
            return "Closed, sir." if closed else f"I see no {target} open, sir."

        # Open application or website
        m = re.search(r"\b(open|launch|start|buka|bukain|jalankan)\b\s+(.+)", t)
        if m:
            target = m.group(2).strip()
            for pattern, cmd in APPS_MAP.items():
                if re.search(rf"\b({pattern})\b", target):
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return "Right away, sir."
            for pattern, url in SITES_MAP.items():
                if re.search(rf"\b({pattern})\b", target):
                    subprocess.Popen(["zen-browser", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return "Opening it now, sir."

        # Screenshot capture
        if re.search(r"\b(screenshot|screen ?sh[oa]+t|skrin ?s[hy]?[uo]+t|tangkap(an)? layar|ss layar)\b", t):
            threading.Thread(target=self._capture_screenshot, daemon=True).start()
            return "Screenshot captured, sir."

        # New wallpaper
        if re.search(r"\b(wallpaper|wall ?paper|latar)\b", t):
            wallpapers_dir = Path.home() / "Pictures/wallpapers"
            subprocess.Popen(["caelestia", "wallpaper", "-r", str(wallpapers_dir)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return "A new wallpaper, sir."

        # Lock screen
        if re.search(r"\b(lock|kunci)\b", t):
            threading.Timer(2.5, self._lock_workstation).start()
            return "Locking the workstation, sir."

        return None

    def _hypr_dispatch(self, command: str) -> None:
        """Execute a hyprctl dispatch command."""
        try:
            subprocess.run(["hyprctl", "dispatch", *command.split()], capture_output=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _capture_screenshot(self) -> None:
        """Hide overlay temporarily and trigger desktop screenshot."""
        if self.dynamic_island:
            subprocess.run(["qs", "-c", self.island_name, "ipc", "call", "island", "idle"], capture_output=True, timeout=3)
        time.sleep(0.8)
        subprocess.run(["caelestia", "screenshot"], capture_output=True, timeout=15)

    def _lock_workstation(self) -> None:
        """Invoke compositor screen locker."""
        subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "lock", "lock"], capture_output=True, timeout=5)

    def _close_named_app(self, name: str) -> bool:
        """Locate window matching name and dispatch close signal."""
        try:
            out = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=5).stdout
            clients = json.loads(out or "[]")
            for c in clients:
                cls = c.get("class", "").lower()
                title = c.get("title", "").lower()
                addr = c.get("address", "")
                if name in cls or name in title:
                    subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{addr}"], capture_output=True)
                    return True
        except Exception:
            pass
        return False
