import subprocess
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger("vidsnap.audio")

MUSIC_CATALOG = {
    "ambient_chill": {
        "id": "ambient_chill",
        "title": "Ambient Chill",
        "genre": "Atmospheric",
        "filename": "1.mp3",
    },
    "upbeat_pulse": {
        "id": "upbeat_pulse",
        "title": "Upbeat Pulse",
        "genre": "Energetic Electronic",
        "filename": "2.mp3",
    },
    "lofi_beat": {
        "id": "lofi_beat",
        "title": "Lo-Fi Dream",
        "genre": "Chillhop",
        "filename": "3.mp3",
    },
}

def get_available_music() -> list[dict]:
    return list(MUSIC_CATALOG.values())

def get_audio_duration(file_path: Path) -> float:
    """
    Returns exact duration of an audio or video file in seconds using ffprobe.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    duration_str = result.stdout.strip()
    try:
        duration = float(duration_str)
        return max(duration, 0.1)
    except ValueError:
        logger.warning(f"Could not parse duration '{duration_str}', defaulting to 5.0")
        return 5.0

