"""Hardware and peripheral observer daemon for proactive system alerts."""

import json
import logging
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Set

logger = logging.getLogger("victor.watcher")

POWER_SUPPLY_PATH = Path("/sys/class/power_supply")
HWMON_PATH = Path("/sys/class/hwmon")


class SystemWatcher:
    """Monitors battery, charger, CPU thermals, memory, disks, and connected devices."""

    def __init__(self, alert_callback: Callable[[str], None], config: Optional[Dict] = None) -> None:
        self.alert_callback = alert_callback
        self.config = config or {}
        self.cooldown_seconds: int = 30 * 60
        self.last_alerts: Dict[str, float] = {}
        self._running: bool = False

        self.low_thresholds = self.config.get("battery_low_thresholds", [20, 10, 5])
        self.phone_low_threshold = self.config.get("phone_low_threshold", 15)
        self.cpu_temp_max = self.config.get("cpu_temp_max_celsius", 90)
        self.ram_min_free = self.config.get("ram_min_free_ratio", 0.07)
        self.disk_min_free = self.config.get("disk_min_free_ratio", 0.10)
        self.quiet_hours = self.config.get("quiet_hours", [22, 7])

    def start(self) -> None:
        """Launch background monitoring threads."""
        self._running = True
        threading.Thread(target=self._run_loop, daemon=True).start()
        threading.Thread(target=self._farewell_listener, daemon=True).start()

    def stop(self) -> None:
        """Stop watcher daemon."""
        self._running = False

    def _run_loop(self) -> None:
        """Periodic hardware evaluation loop."""
        pct, plugged = self.get_battery_status()
        warned_battery: Set[int] = {x for x in self.low_thresholds if pct <= x}
        consecutive_hot_ticks = 0
        current_audio = self.get_audio_sink_type()
        current_bt = self.get_connected_bluetooth()
        current_monitors = self.get_monitor_count()
        tick = 0

        while self._running:
            time.sleep(5)
            tick += 1

            # 1. Battery, AC adapter, and power profile adjustments
            new_pct, new_plugged = self.get_battery_status()
            if new_plugged != plugged:
                profile = "balanced" if new_plugged else "power-saver"
                subprocess.run(["powerprofilesctl", "set", profile], capture_output=True)
                if new_plugged:
                    self._emit_alert(f"Charger connected, sir. Battery at {new_pct} percent.")
                else:
                    self._emit_alert(f"Running on battery power, sir. {new_pct} percent remaining. Power saver engaged.")
                warned_battery = set()
            elif not new_plugged:
                for threshold in self.low_thresholds:
                    if new_pct <= threshold and threshold not in warned_battery:
                        warned_battery.update(t for t in self.low_thresholds if t >= threshold)
                        if threshold > 5:
                            self._emit_alert(f"Battery at {new_pct} percent, sir. I suggest plugging in.")
                        else:
                            self._emit_alert(f"Battery critical at {new_pct} percent, sir. Shutdown is imminent.")
                        break
            pct, plugged = new_pct, new_plugged

            # 2. CPU Thermals (Require 3 consecutive ticks = 15 seconds)
            temp = self.get_cpu_temperature()
            if temp >= self.cpu_temp_max:
                consecutive_hot_ticks += 1
            else:
                consecutive_hot_ticks = 0

            if consecutive_hot_ticks == 3:
                self._emit_cooldown("temp", f"CPU temperature is at {temp} degrees, sir. You may want to ease off.")

            # 3. RAM & Storage Free Margins
            if self.get_ram_free_ratio() < self.ram_min_free:
                self._emit_cooldown("ram", "System memory is almost full, sir. Consider closing a few applications.")

            disk_free_ratio = self.get_disk_free_ratio("/")
            if disk_free_ratio < self.disk_min_free:
                pct_free = int(disk_free_ratio * 100)
                self._emit_cooldown("disk", f"Disk space is down to {pct_free} percent, sir.")

            # 4. Monitors and Audio Outputs
            n_monitors = self.get_monitor_count()
            if n_monitors != current_monitors and n_monitors > 0:
                self._emit_alert("External display connected, sir." if n_monitors > current_monitors else "External display disconnected, sir.")
                current_monitors = n_monitors

            audio_sink = self.get_audio_sink_type()
            if audio_sink and audio_sink != current_audio:
                self._emit_alert("Headphones connected, sir." if audio_sink == "headphones" else "Switched to speakers, sir.")
                current_audio = audio_sink

            bt_devices = self.get_connected_bluetooth()
            for dev in sorted(bt_devices - current_bt):
                self._emit_alert(f"{dev} connected, sir.")
            current_bt = bt_devices

    def _emit_alert(self, text: str) -> None:
        """Dispatch verbal notification if not within quiet hours."""
        if not self._is_quiet_hours():
            self.alert_callback(text)

    def _emit_cooldown(self, key: str, text: str) -> None:
        """Dispatch verbal notification respecting cooldown intervals."""
        now = time.time()
        if now - self.last_alerts.get(key, 0.0) > self.cooldown_seconds:
            self.last_alerts[key] = now
            self._emit_alert(text)

    def _is_quiet_hours(self) -> bool:
        """Check if current time falls within user-configured quiet hours."""
        h = time.localtime().tm_hour
        return h >= self.quiet_hours[0] or h < self.quiet_hours[1]

    def _farewell_listener(self) -> None:
        """Inhibit shutdown briefly to pronounce farewell greeting."""
        try:
            inhibit = subprocess.Popen([
                "systemd-inhibit", "--what=shutdown", "--mode=delay",
                "--who=Victor", "--why=Farewell", "sleep", "infinity"
            ])
            mon = subprocess.Popen([
                "dbus-monitor", "--system",
                "type='signal',interface='org.freedesktop.login1.Manager',member='PrepareForShutdown'"
            ], stdout=subprocess.PIPE, text=True)

            if mon.stdout:
                for line in mon.stdout:
                    if "boolean true" in line:
                        self.alert_callback("Goodbye, sir. Shutting down.")
                        time.sleep(2)
                        inhibit.kill()
                        return
        except Exception:
            pass

    @staticmethod
    def get_battery_status() -> tuple[int, bool]:
        """Read BAT0 capacity and AC adapter status."""
        try:
            cap_file = POWER_SUPPLY_PATH / "BAT0/capacity"
            ac_file = POWER_SUPPLY_PATH / "ACAD/online"
            capacity = int(cap_file.read_text().strip()) if cap_file.exists() else 100
            plugged = (ac_file.read_text().strip() == "1") if ac_file.exists() else True
            return capacity, plugged
        except Exception:
            return 100, True

    @staticmethod
    def get_cpu_temperature() -> int:
        """Query CPU temperature sensor from hwmon."""
        try:
            for h in HWMON_PATH.iterdir():
                name_file = h / "name"
                if name_file.exists() and name_file.read_text().strip() in ("k10temp", "coretemp"):
                    temp_input = h / "temp1_input"
                    if temp_input.exists():
                        return int(temp_input.read_text().strip()) // 1000
        except Exception:
            pass
        return 0

    @staticmethod
    def get_ram_free_ratio() -> float:
        """Calculate available memory ratio from /proc/meminfo."""
        try:
            lines = Path("/proc/meminfo").read_text().splitlines()
            info = dict(l.split(":", 1) for l in lines)
            avail = int(info["MemAvailable"].split()[0])
            total = int(info["MemTotal"].split()[0])
            return avail / total
        except Exception:
            return 1.0

    @staticmethod
    def get_disk_free_ratio(path: str = "/") -> float:
        """Calculate disk free ratio for specified mount point."""
        try:
            du = shutil.disk_usage(path)
            return du.free / du.total
        except Exception:
            return 1.0

    @staticmethod
    def get_monitor_count() -> int:
        """Query Hyprland active monitor count."""
        try:
            out = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=3).stdout
            return len(json.loads(out or "[]"))
        except Exception:
            return 0

    @staticmethod
    def get_audio_sink_type() -> str:
        """Detect active audio sink type (headphones vs speakers)."""
        try:
            default_sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=2).stdout.strip()
            sinks_json = subprocess.run(["pactl", "-f", "json", "list", "sinks"], capture_output=True, text=True, timeout=2).stdout
            sinks = json.loads(sinks_json or "[]")
            for s in sinks:
                if s.get("name") == default_sink:
                    port = s.get("active_port", "").lower()
                    return "headphones" if "headphone" in port or "bluez" in default_sink else "speakers"
        except Exception:
            pass
        return ""

    @staticmethod
    def get_connected_bluetooth() -> Set[str]:
        """Fetch set of currently connected Bluetooth devices."""
        try:
            out = subprocess.run(["bluetoothctl", "devices", "Connected"], capture_output=True, text=True, timeout=3).stdout
            return {
                l.split(" ", 2)[2]
                for l in out.splitlines()
                if l.startswith("Device ") and len(l.split(" ", 2)) == 3
            }
        except Exception:
            return set()
