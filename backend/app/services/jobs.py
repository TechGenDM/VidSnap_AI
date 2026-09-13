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

def process_quick_reel_job(job_id: str):
    """
    Background worker function executing the full Quick Reel vertical slice.
    """
    job = db.get_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in database.")
        return

    project = db.get_project(job.project_id)
    if not project:
        logger.error(f"Project {job.project_id} not found.")
        job.status = JobStatus.FAILED
        job.error_message = "Associated project was not found."
        job.updated_at = now_iso()
        db.save_job(job)
        return

    project_dir = get_project_dir(project.id)
    temp_dir = project_dir / "temp"

    try:
        # STEP 1: Processing
        job.status = JobStatus.PROCESSING
        job.step = "Analyzing your story & assets"
        job.progress_percent = 15
        job.updated_at = now_iso()
        db.save_job(job)
        time.sleep(0.3)

        # Gather images in designated scene order
        image_paths = []
        for scene in project.scenes:
            img_file = project_dir / scene.visual_filename
            if img_file.exists():
                image_paths.append(img_file)

        if not image_paths:
            raise ValueError("No uploaded images found in project directory.")

        # STEP 2: Generating Voice Narration
        job.status = JobStatus.GENERATING_VOICE
        job.step = "Synthesizing voice narration"
        job.progress_percent = 35
        job.updated_at = now_iso()
        db.save_job(job)

        raw_voice_path = project_dir / "voice_raw.mp3"
