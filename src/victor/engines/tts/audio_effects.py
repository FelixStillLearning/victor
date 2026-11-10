"""Audio digital signal processing and visual envelope calculation."""

import array
import subprocess
import wave
from typing import List, Tuple

DEFAULT_FILTER_GRAPH = "highpass=f=120,aecho=0.8:0.6:40|70:0.25|0.15,volume=1.2"


def apply_audio_filter(input_wav: str, output_wav: str, filter_graph: str = DEFAULT_FILTER_GRAPH) -> bool:
    """Process WAV audio file through FFmpeg filter chain."""
    try:
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", input_wav, "-af", filter_graph, output_wav]
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def calculate_envelope(wav_path: str) -> Tuple[List[float], int]:
    """Calculate normalized 50ms RMS amplitude buckets for dynamic island visualizer."""
    try:
        with wave.open(wav_path, "rb") as w:
            rate = w.getframerate()
            frames = w.readframes(w.getnframes())

        pcm = array.array("h", frames)
        step = rate // 20
        rms = [
            (sum(x * x for x in pcm[i:i + step:4]) / max(1, len(pcm[i:i + step:4]))) ** 0.5
            for i in range(0, len(pcm), step)
        ]
        peak = max(rms or [1.0]) or 1.0
        normalized = [round(r / peak, 2) for r in rms]
        duration_ms = len(pcm) * 1000 // rate
        return normalized, duration_ms
    except Exception:
        return [], 0
