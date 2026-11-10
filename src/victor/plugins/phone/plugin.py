"""Phone and KDE Connect plugin implementation."""

import re
import subprocess
from typing import Any, Dict, Optional, Tuple

from victor.plugins.base import VictorPlugin


class PhonePlugin(VictorPlugin):
    """Integrates mobile device ringing and telemetry via KDE Connect."""

    name = "phone"
    description = "KDE Connect phone locator"
    keywords = ["find my phone", "cari hp", "where is my phone", "ring phone"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        if re.search(r"\b(find|cari|where is|di ?mana|ring)\b.*\b(phone|hp|handphone|ponsel)\b", t):
            dev_id, dev_name = self._find_connected_phone()
            if not dev_id:
                return "I cannot reach your phone, sir."
            subprocess.run(["kdeconnect-cli", "-d", dev_id, "--ring"], capture_output=True)
            return "Ringing your phone now, sir."

        return None

    def _find_connected_phone(self) -> Tuple[Optional[str], Optional[str]]:
        """Identify first connected KDE Connect mobile node."""
        try:
            out = subprocess.run(["kdeconnect-cli", "-a", "--id-name-only"],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
            lines = out.splitlines()
            if lines and " " in lines[0]:
                parts = lines[0].split(" ", 1)
                return parts[0], parts[1]
        except Exception:
            pass
        return None, None
