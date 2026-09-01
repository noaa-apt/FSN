import subprocess
import tempfile
import os
from pathlib import Path

def record_from_kiwi(host: str, port: int, freq_khz: float,
                     duration_sec: int = 120, mode: str = "usb") -> str:
    out = tempfile.mktemp(suffix=".wav")
    cmd = [
        "python3", "-u", "kiwirecorder.py",
        "-s", host, "-p", str(port),
        "-f", str(freq_khz),
        "-m", mode,
        "--tlimit", str(duration_sec),
        "-w", out
    ]
    print("Running:", " ".join(cmd))
    return out
