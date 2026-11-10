"""Command history and recall plugin implementation."""

import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from victor.core.ipc import ensure_state_dir
from victor.plugins.base import VictorPlugin


class HistoryPlugin(VictorPlugin):
    """Logs executed commands and answers conversational recall inquiries."""

    name = "history"
    description = "Command audit logging and conversational recall"
    keywords = ["history", "riwayat", "what did i ask", "tadi aku tanya apa", "tadi aku minta apa"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        state_dir = ensure_state_dir()
        self.db_path = state_dir / "history.db"
        self._init_database()
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        # Recall queries: "what did I ask earlier?", "tadi aku tanya apa?"
        if re.search(r"\b(what did i (ask|say|request)|tadi (aku|saya) (tanya|minta|bilang) apa)\b", t):
            recent = self._get_recent_entries(limit=3)
            if not recent:
                return "I have no record of prior commands in this session, sir."
            formatted = "; ".join(f"'{entry[1]}'" for entry in recent if entry[1] != intent)
            return f"Earlier you requested: {formatted}, sir." if formatted else "I recorded only your current inquiry, sir."

        # If not a recall query, log this intent as an executed command
        self._log_command(intent, context.get("response", ""))
        return None

    def _init_database(self) -> None:
        """Create the commands table if not present."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS command_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        intent TEXT,
                        response TEXT
                    )
                """)
        except Exception:
            pass

    def _log_command(self, intent: str, response: str) -> None:
        """Persist command event to SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO command_history (timestamp, intent, response) VALUES (?, ?, ?)",
                    (time.time(), intent, response),
                )
        except Exception:
            pass

    def _get_recent_entries(self, limit: int = 5) -> List[Tuple[int, str, str]]:
        """Fetch most recent command history entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    "SELECT id, intent, response FROM command_history ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
                return cur.fetchall()
        except Exception:
            return []
