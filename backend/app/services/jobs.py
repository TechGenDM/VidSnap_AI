import re
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models import Job, Project, JobStatus, Scene
from app.database import db
from app.services.ai import tts_service
from app.services.audio import get_audio_duration, mix_voice_and_music
from app.services.video import render_reel_video, generate_video_thumbnail
from app.services.storage import get_project_dir

logger = logging.getLogger("vidsnap.jobs")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def split_script_into_captions(script: str, num_scenes: int) -> list[str]:
    """
    Intelligently splits narration script into readable captions across scenes.
    """
    sentences = re.split(r"[.!?]+", script)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [f"Scene {i+1}" for i in range(num_scenes)]

    if len(sentences) == num_scenes:
        return sentences

    if len(sentences) > num_scenes:
        # Group sentences evenly
        chunk_size = len(sentences) / num_scenes
        captions = []
        for i in range(num_scenes):
            start = int(i * chunk_size)
            end = int((i + 1) * chunk_size)
            captions.append(" ".join(sentences[start:end]))
        return captions

    # Fewer sentences than scenes: divide sentences by clauses/words
    words = script.split()
    words_per_scene = max(1, len(words) // num_scenes)
    captions = []
    for i in range(num_scenes):
        start = i * words_per_scene
        end = (i + 1) * words_per_scene if i < num_scenes - 1 else len(words)
        captions.append(" ".join(words[start:end]))
    return captions

