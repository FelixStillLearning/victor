"""Inter-Process Communication (IPC) helpers for Quickshell dynamic island and locks."""

import fcntl
import os
import subprocess
from pathlib import Path
from typing import Optional, Sequence

RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
LOCK_FILE = RUNTIME_DIR / "victor.lock"
SPEAKING_FLAG = RUNTIME_DIR / "victor-speaking"
LISTEN_PID_FILE = RUNTIME_DIR / "victor-listen.pid"
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "victor"
LISTEN_OFF_FLAG = STATE_DIR / "listen-off"


def ensure_state_dir() -> Path:
    """Ensure the user state directory exists and return it."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def notify_island(component: str, *args: Sequence[str]) -> bool:
    """Send an IPC command to Quickshell dynamic island."""
    try:
        cmd = ["qs", "-c", component, "ipc", "call", "island"] + [str(a) for a in args]
        subprocess.run(cmd, capture_output=True, timeout=3)
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def is_speaking() -> bool:
    """Return True if Victor is currently synthesizing and playing audio."""
    return SPEAKING_FLAG.exists()


class SpeakingLock:
    """Context manager to ensure speech playback exclusivity."""

    def __init__(self) -> None:
        self._fd: Optional[int] = None

    def __enter__(self) -> None:
        self._fd = os.open(LOCK_FILE, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        SPEAKING_FLAG.touch()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            SPEAKING_FLAG.unlink(missing_ok=True)
        finally:
            if self._fd is not None:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
                self._fd = None
