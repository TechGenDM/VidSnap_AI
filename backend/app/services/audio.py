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

