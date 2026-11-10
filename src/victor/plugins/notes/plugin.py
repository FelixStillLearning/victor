"""Notes and Obsidian plugin implementation."""

import re
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from victor.plugins.base import VictorPlugin


class NotesPlugin(VictorPlugin):
    """Appends quick notes into Obsidian daily notes vault."""

    name = "notes"
    description = "Obsidian daily note writer"
    keywords = ["catat", "catet", "note", "take a note", "tulis catatan"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        obsidian_cfg = config.get("obsidian", {})
        self.vault_path = obsidian_cfg.get("vault_path") or config.get("vault_path", "")
        self.daily_dir = obsidian_cfg.get("daily_notes_dir", "")
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        m = re.match(r"(?:catat|catet|tulis catatan|take a note|note that|note)\b[:,]?\s*(.*)", t)
        if m:
            content = m.group(1).strip()
            if not content:
                return "What shall I note, sir?"
            self._write_note(content)
            return "Noted, sir."

        return None

    def _write_note(self, text: str) -> None:
        """Append timestamped note into today's markdown file."""
        candidates = []
        if self.vault_path:
            v_path = Path(self.vault_path).expanduser()
            if self.daily_dir:
                candidates.append(v_path / self.daily_dir)
            candidates.append(v_path)

        candidates.extend([
            Path.home() / "Documents/Obsidian",
            Path.home() / "Obsidian",
            Path.home() / "FELIXRDEV",
        ])

        target_dir = None
        for candidate in candidates:
            if candidate.is_dir():
                target_dir = candidate
                break

        if not target_dir:
            target_dir = Path.home() / "Notes"
            target_dir.mkdir(parents=True, exist_ok=True)

        today_file = target_dir / f"{date.today().isoformat()}.md"
        time_str = time.strftime("%H:%M")
        line = f"- {time_str} {text}\n"

        try:
            with today_file.open("a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass
