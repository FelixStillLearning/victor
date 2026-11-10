"""Subcommand execution handlers for V.I.C.T.O.R. CLI."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Tuple

from victor.core.config import get_config
from victor.core.ipc import (
    LISTEN_OFF_FLAG,
    LISTEN_PID_FILE,
    SpeakingLock,
    ensure_state_dir,
    notify_island,
)
from victor.core.persona import NUMBERS_MAP
from victor.core.router import IntentRouter
from victor.core.watcher import SystemWatcher
from victor.engines.llm.claude_cli import ClaudeCLIEngine
from victor.engines.llm.ollama import OllamaEngine
from victor.engines.stt.faster_whisper import FasterWhisperEngine
from victor.engines.tts.audio_effects import calculate_envelope
from victor.engines.tts.piper import PiperTTSEngine
from victor.engines.wakeword.openwakeword import OpenWakeWordEngine
from victor.plugins.clipboard import ClipboardPlugin
from victor.plugins.history import HistoryPlugin
from victor.plugins.hyprland import HyprlandPlugin
from victor.plugins.media import MediaPlugin
from victor.plugins.notes import NotesPlugin
from victor.plugins.phone import PhonePlugin
from victor.plugins.registry import get_registry
from victor.plugins.tasks import TasksPlugin
from victor.plugins.vision import VisionPlugin


def setup_runtime() -> Tuple[IntentRouter, PiperTTSEngine]:
    """Assemble engines, registry, and intent router from active configuration."""
    cfg = get_config()
    reg = get_registry()

    # Initialize bundled plugins
    plugins = [
        HyprlandPlugin(),
        MediaPlugin(),
        TasksPlugin(),
        NotesPlugin(),
        PhonePlugin(),
        VisionPlugin(),
        ClipboardPlugin(),
        HistoryPlugin(),
    ]
    for p in plugins:
        p_cfg = cfg.get(f"plugins.{p.name}", {})
        reg.register(p, p_cfg)

    # Initialize LLM engine
    llm_type = cfg.get("engines.llm", "claude_cli")
    llm_engine = None
    if llm_type == "ollama":
        llm_engine = OllamaEngine()
        llm_engine.initialize(cfg.get("engines.ollama", {}))
    else:
        llm_engine = ClaudeCLIEngine()
        llm_engine.initialize(cfg.get("engines.claude_cli", {}))

    router = IntentRouter(registry=reg, llm=llm_engine)

    # Initialize TTS engine
    tts = PiperTTSEngine()
    tts.initialize(cfg.get("engines.piper", {}))

    return router, tts


def speak(text: str, tts: Optional[PiperTTSEngine] = None) -> None:
    """Synthesize and vocalize a spoken sentence synchronously."""
    if not text.strip():
        return
    cfg = get_config()
    engine = tts
    if engine is None:
        engine = PiperTTSEngine()
        engine.initialize(cfg.get("engines.piper", {}))

    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = f"{tmp_dir}/out.wav"
        if engine.synthesize_to_file(text, wav_path):
            with SpeakingLock():
                env, duration_ms = calculate_envelope(wav_path)
                island_component = cfg.get("plugins.hyprland.dynamic_island_component", "jarvis-island")
                if env:
                    notify_island(island_component, "speak", text, ",".join(map(str, env)), duration_ms)
                subprocess.run(["pw-play", wav_path], check=False)


def speak_async(text: str) -> None:
    """Trigger non-blocking speech playback in a background thread."""
    threading.Thread(target=speak, args=(text,), daemon=True).start()


def cmd_say(text: str) -> None:
    """Execute 'victor say <text>'."""
    speak(text)


def cmd_greet() -> None:
    """Execute 'victor greet' on login."""
    state_dir = ensure_state_dir()
    stamp = state_dir / "last-greet"
    today_str = date.today().isoformat()

    first_today = True
    if stamp.exists() and stamp.read_text().strip() == today_str:
        first_today = False
    stamp.write_text(today_str)

    cfg = get_config()
    city = cfg.get("location.city", "Jakarta")
    user_name = cfg.get("user.honorific", "sir")

    now = datetime.now()
    part = "morning" if 4 <= now.hour < 12 else "afternoon" if 12 <= now.hour < 18 else "evening"

    if not first_today:
        speak(f"Good {part}, {user_name}. Welcome back.")
        return

    # First login greeting of the day
    lines = [f"Good {part}, {user_name}. All systems are online."]
    if city:
        try:
            with urllib.request.urlopen(f"https://wttr.in/{urllib.request.quote(city)}?format=j1", timeout=3) as r:
                cur = json.load(r)["current_condition"][0]
                lines.append(f"It is {cur['temp_C']} degrees outside, {cur['weatherDesc'][0]['value'].strip().lower()}.")
        except Exception:
            pass

    speak(" ".join(lines))


def cmd_brief() -> None:
    """Execute 'victor brief' (Super+J)."""
    cfg = get_config()
    user = cfg.get("user.honorific", "sir")
    now = datetime.now()
    hour = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"
    time_str = f"{hour}:{now.minute:02d} {ampm}"

    pct, plugged = SystemWatcher.get_battery_status()
    batt_str = f"Battery at {pct} percent{', charging' if plugged else ''}."

    speak(f"It is {time_str}, {user}. {batt_str}")


def cmd_done(status: str, pid: str, command_line: str) -> None:
    """Execute 'victor done <status> <pid> <cmd>' invoked by terminal shell hooks."""
    try:
        active_pid = json.loads(subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True).stdout or "{}").get("pid")
    except Exception:
        active_pid = None

    p = int(pid)
    while p > 1:
        if p == active_pid:
            return
        try:
            stat_line = Path(f"/proc/{p}/stat").read_text()
            p = int(stat_line.rsplit(")", 1)[-1].split()[1])
        except Exception:
            break

    name = command_line.split()[0].split("/")[-1] if command_line.strip() else "command"
    if name in ("sudo", "doas") and len(command_line.split()) > 1:
        name = command_line.split()[1]

    if status == "0":
        speak(f"The {name} command has finished, sir.")
    else:
        speak(f"The {name} command has failed, sir.")


def cmd_toggle() -> None:
    """Toggle wake-word listening on or off."""
    ensure_state_dir()
    if LISTEN_OFF_FLAG.exists():
        LISTEN_OFF_FLAG.unlink()
        speak("Listening enabled, sir.")
    else:
        LISTEN_OFF_FLAG.touch()
        speak("Listening disabled, sir.")


def cmd_ask() -> None:
    """Trigger single-shot listening without hotword."""
    if LISTEN_PID_FILE.exists():
        try:
            pid = int(LISTEN_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGUSR1)
            return
        except Exception:
            pass
    speak("My listening module is offline, sir.")


def cmd_watch() -> None:
    """Start hardware and peripheral monitor daemon."""
    cfg = get_config()
    watcher = SystemWatcher(alert_callback=speak_async, config=cfg.get("system_watch", {}))
    watcher.start()
    while True:
        time.sleep(1)


def cmd_listen() -> None:
    """Start continuous wake-word and audio recognition loop."""
    import numpy as np
    cfg = get_config()
    router, tts = setup_runtime()

    wake_engine = OpenWakeWordEngine()
    wake_engine.initialize(cfg.get("engines.openwakeword", {}))

    stt_engine = FasterWhisperEngine()
    stt_engine.initialize(cfg.get("engines.faster_whisper", {}))

    ensure_state_dir()
    LISTEN_PID_FILE.write_text(str(os.getpid()))

    # Run parec audio stream
    parec = subprocess.Popen(
        ["parec", "--raw", "--rate=16000", "--channels=1", "--format=s16le"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    CHUNK_SIZE = 1280  # 80ms at 16kHz
    try:
        while True:
            raw_chunk = parec.stdout.read(CHUNK_SIZE * 2) if parec.stdout else b""
            if not raw_chunk:
                time.sleep(0.01)
                continue

            if LISTEN_OFF_FLAG.exists():
                time.sleep(0.5)
                continue

            chunk_arr = np.frombuffer(raw_chunk, dtype=np.int16)
            score = wake_engine.predict(chunk_arr)
            if score >= cfg.get("engines.openwakeword.threshold", 0.5):
                island_name = cfg.get("plugins.hyprland.dynamic_island_component", "jarvis-island")
                notify_island(island_name, "hear")

                # Collect speech segment (2.5 seconds)
                audio_frames = [raw_chunk]
                for _ in range(30):
                    audio_frames.append(parec.stdout.read(CHUNK_SIZE * 2) if parec.stdout else b"")

                full_pcm = np.frombuffer(b"".join(audio_frames), dtype=np.int16).astype(np.float32) / 32768.0
                notify_island(island_name, "think")
                transcription = stt_engine.transcribe(full_pcm)

                if transcription:
                    response = router.route(transcription)
                    speak(response, tts)
                else:
                    notify_island(island_name, "idle")
    finally:
        parec.kill()
        LISTEN_PID_FILE.unlink(missing_ok=True)
