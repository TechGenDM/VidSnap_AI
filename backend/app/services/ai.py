import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger("vidsnap.ai")

VOICE_MAP = {
    "adam": {
        "id": "pNInz6obpgDQGcFmaJgB",
        "name": "Adam",
        "gender": "Male",
        "accent": "Deep & Narrative",
        "macos_voice": "Alex",
    },
    "rachel": {
        "id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel",
        "gender": "Female",
        "accent": "Warm & Engaging",
        "macos_voice": "Samantha",
    },
    "josh": {
        "id": "TxGEqnHWrfWFTfGW9XjX",
        "name": "Josh",
        "gender": "Male",
        "accent": "Young & Energetic",
        "macos_voice": "Fred",
    },
    "antoni": {
        "id": "ErXwobaYiN019PkySvjV",
        "name": "Antoni",
        "gender": "Male",
        "accent": "Thoughtful & Crisp",
        "macos_voice": "Daniel",
    },
}

def get_available_voices() -> list[dict]:
    return [
        {
            "id": k,
            "name": v["name"],
            "gender": v["gender"],
            "accent": v["accent"],
            "description": f"{v['gender']} • {v['accent']}",
        }
        for k, v in VOICE_MAP.items()
    ]

