"""Media and Spotify controller plugin implementation."""

import base64
import json
import re
import subprocess
import threading
import urllib.request
from typing import Any, Dict, Optional, Tuple

from victor.plugins.base import VictorPlugin


class MediaPlugin(VictorPlugin):
    """Handles playback state, volume levels, and Spotify catalog search."""

    name = "media"
    description = "MPRIS playback and Spotify catalog integration"
    keywords = ["play", "putar", "pause", "jeda", "next", "previous", "volume"]

    def setup(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.client_id = config.get("spotify_client_id", "")
        self.client_secret = config.get("spotify_client_secret", "")
        self._spotify_token: Optional[str] = None
        return True

    def handle(self, intent: str, context: Dict[str, Any]) -> Optional[str]:
        t = intent.lower().strip(" .!?")

        # Play specific track on Spotify
        m = re.search(r"\b(putar|puterin|play|mainkan|setel|setelin)\b\s+(?:(?:lagu|song|the song)\s+)?(.+)", t)
        if m and not re.fullmatch(r"(lagu|lagunya|musik|music|spotify|lagi|again|the music|lanjut)( lagi)?", m.group(2)) \
                and not re.search(r"\b(next|previous|berikutnya|sebelumnya|selanjutnya)\b", t):
            query = re.sub(r"\b(di|on|in) spotify\b", "", m.group(2)).strip()
            uri, name = self._search_spotify(query)
            threading.Thread(target=self._open_spotify_uri, args=(uri or f"spotify:search:{query}",), daemon=True).start()
            return f"Playing {name}, sir." if uri else f"Searching Spotify for {query}, sir."

        # Navigation controls
        if re.search(r"\b(next|skip|berikutnya|selanjutnya|ganti lagu)\b", t):
            self._mpris_action("next")
            return "Next track, sir."
        if re.search(r"\b(previous|sebelumnya)\b", t):
            self._mpris_action("previous")
            return "Previous track, sir."
        if re.search(r"\b(pause|stop|jeda|hentikan)\b", t):
            self._mpris_action("pause")
            return "Paused, sir."
        if re.search(r"\b(play|resume|putar|puterin|lanjutkan)\b", t):
            self._mpris_action("play")
            return "Playing, sir."

        # Volume controls
        if re.search(r"\b(volume up|louder|keraskan|kerasin|naikkan|naikin)\b", t):
            subprocess.run(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", "10%+"], capture_output=True)
            return "Volume up, sir."
        if re.search(r"\b(volume down|quieter|kecilkan|kecilin|pelankan|turunkan|turunin)\b", t):
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%-"], capture_output=True)
            return "Volume down, sir."

        return None

    def _mpris_action(self, action: str) -> None:
        """Trigger MPRIS playback action via Quickshell or playerctl."""
        try:
            subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "mpris", action], capture_output=True, timeout=2)
        except Exception:
            subprocess.run(["playerctl", action], capture_output=True)

    def _search_spotify(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Query Spotify Web API for track URI and metadata."""
        if not self.client_id or not self.client_secret:
            return None, None
        try:
            auth_str = f"{self.client_id}:{self.client_secret}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            token_req = urllib.request.Request(
                "https://accounts.spotify.com/api/token",
                data=b"grant_type=client_credentials",
                headers={"Authorization": f"Basic {b64_auth}", "Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(token_req, timeout=5) as r:
                token = json.load(r).get("access_token")

            encoded_query = urllib.request.quote(query)
            search_req = urllib.request.Request(
                f"https://api.spotify.com/v1/search?type=track&limit=1&q={encoded_query}",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(search_req, timeout=5) as r:
                data = json.load(r)
                items = data.get("tracks", {}).get("items", [])
                if items:
                    track = items[0]
                    artists = ", ".join(a["name"] for a in track.get("artists", []))
                    name = f"{track['name']} by {artists}" if artists else track["name"]
                    return track["uri"], name
        except Exception:
            pass
        return None, None

    def _open_spotify_uri(self, uri: str) -> None:
        """Open Spotify URI via Caelestia or desktop opener."""
        subprocess.run(["caelestia", "spotify", uri], capture_output=True)
