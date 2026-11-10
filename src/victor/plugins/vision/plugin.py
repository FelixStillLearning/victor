"""Vision and active window contextual inspection plugin."""

import re
from typing import Any, Dict, Optional

from victor.plugins.base import VictorPlugin
from victor.plugins.vision.atspi_reader import AtspiReader


class VisionPlugin(VictorPlugin):
    """Provides semantic screen context and visual document summarization."""

    name = "vision"
    description = "Active window context and AT-SPI semantic inspection"
    keywords = [
        "read screen",
        "baca layar",
        "what is on my screen",
        "summarize this document",
        "ringkas dokumen",
        "jelaskan error",
    ]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.reader = AtspiReader()
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        if re.search(r"\b(read screen|baca layar|what is on (the|my) screen|apa yang ada di layar)\b", t):
            ctx = self.reader.get_active_window_context()
            title = ctx.get("title", "")
            app_cls = ctx.get("class", "")
            content = ctx.get("content", "")

            if not title and not app_cls:
                return "There are no active windows currently focused, sir."

            summary = f"You are currently viewing {title} in {app_cls}."
            if content:
                snippet = content[:150].strip()
                return f"{summary} I observe text regarding: {snippet}."
            return f"{summary}, sir."

        if re.search(r"\b(summarize (this )?(document|page|pdf)|ringkas (dokumen|halaman) ini)\b", t):
            ctx = self.reader.get_active_window_context()
            title = ctx.get("title", "")
            content = ctx.get("content", "")
            if content:
                return f"The active document '{title}' discusses: {content[:200]}."
            return f"I see the document titled '{title}', but full text extraction is unavailable via the accessibility bus, sir."

        return None
