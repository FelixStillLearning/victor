"""Anthropic Claude Code CLI adapter implementation."""

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from victor.core.ipc import ensure_state_dir
from victor.engines.llm.base import LLMEngine


class ClaudeCLIEngine(LLMEngine):
    """Executes queries via local Claude Code CLI binary."""

    def __init__(self) -> None:
        self.executable: str = "claude"
        self.model: str = "haiku"

    def initialize(self, config: Dict[str, Any]) -> bool:
        self.executable = config.get("executable", "claude")
        self.model = config.get("model", "haiku")

        resolved = shutil.which(self.executable) or str(Path.home() / ".local/bin/claude")
        return Path(resolved).exists() or shutil.which("claude") is not None

    def query(self, prompt: str, system_prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> str:
        state_dir = ensure_state_dir()
        work_dir = state_dir / "claude"
        work_dir.mkdir(parents=True, exist_ok=True)

        nomcp = work_dir / "no-mcp.json"
        if not nomcp.exists():
            nomcp.write_text('{"mcpServers": {}}')

        exe = shutil.which(self.executable) or str(Path.home() / ".local/bin/claude")
        cmd = [
            exe,
            "-p",
            "--model", self.model,
            "--tools", "",
            "--no-session-persistence",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config", str(nomcp),
            "--setting-sources", "project,local",
            "--system-prompt", system_prompt,
            prompt,
        ]

        try:
            res = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, timeout=45)
            out = res.stdout.strip()
            return out.replace("*", "").strip()
        except (OSError, subprocess.TimeoutExpired):
            return ""
