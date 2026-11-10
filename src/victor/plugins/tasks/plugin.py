"""Tasks and Todoist plugin implementation."""

import json
import re
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from victor.plugins.base import VictorPlugin

DUE_PATTERNS: List[Tuple[str, str]] = [
    (r"hari ini|today", "today"),
    (r"besok|tomorrow", "tomorrow"),
    (r"lusa", "in 2 days"),
    (r"minggu depan|next week", "next week"),
    (r"senin|monday", "monday"),
    (r"selasa|tuesday", "tuesday"),
    (r"rabu|wednesday", "wednesday"),
    (r"kamis|thursday", "thursday"),
    (r"jumat|jum'at|friday", "friday"),
    (r"sabtu|saturday", "saturday"),
    (r"minggu|ahad|sunday", "sunday"),
]


class TasksPlugin(VictorPlugin):
    """Manages tasks via Todoist REST API."""

    name = "tasks"
    description = "Todoist task management"
    keywords = ["tambah tugas", "add task", "buat tugas", "todo"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.token = config.get("todoist", {}).get("api_token") or config.get("api_token", "")
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        m = re.search(r"\b(?:(?:tambah(?:kan)?|tambahin|bikin|buat(?:kan)?|add)\s+(?:a\s+)?(?:tugas|task|to ?do))\b[:,]?\s*(.*)", t)
        if m:
            content = m.group(1).strip()
            return self._add_todoist_task(content)

        return None

    def _add_todoist_task(self, text: str) -> str:
        """Parse natural due date and post task to Todoist."""
        if not self.token:
            return "Todoist token is not configured, sir."

        due_string = None
        for pattern, due in DUE_PATTERNS:
            match = re.search(rf"\b({pattern})\b", text)
            if match:
                due_string = due
                text = (text[:match.start()] + text[match.end():]).strip()
                break

        body: Dict[str, Any] = {"content": text[:1].upper() + text[1:] if text else "New Task"}
        if due_string:
            body["due_string"] = due_string

        req = urllib.request.Request(
            "https://api.todoist.com/api/v1/tasks",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=8):
                pass
            return f"Added '{body['content']}' to your tasks{' for ' + due_string if due_string else ''}, sir."
        except Exception:
            return "I could not reach Todoist, sir."
