import re
import time
import shutil
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
        tts_service.generate_speech(
            text=project.script,
            voice_key=project.voice,
            output_path=raw_voice_path,
        )

        # Detect real narration audio duration
        voice_duration = get_audio_duration(raw_voice_path)
        logger.info(f"Generated voiceover duration: {voice_duration:.2f} seconds")

        # STEP 3: Audio Balancing & Ducking
        job.step = "Balancing speech & background music"
        job.progress_percent = 50
        job.updated_at = now_iso()
        db.save_job(job)

        final_audio_path = project_dir / "audio_final.aac"
        mix_voice_and_music(
            voice_path=raw_voice_path,
            music_key=project.music,
            output_path=final_audio_path,
        )

        # STEP 4: Captions & Story Timing
        job.status = JobStatus.GENERATING_CAPTIONS
        job.step = "Designing kinetic captions & scene timing"
        job.progress_percent = 65
        job.updated_at = now_iso()
        db.save_job(job)

        captions = split_script_into_captions(project.script, len(image_paths))

        # STEP 5: Video Rendering
        job.status = JobStatus.RENDERING
        job.step = "Compositing 1080x1920 Reel with motion & blurred framing"
        job.progress_percent = 80
        job.updated_at = now_iso()
        db.save_job(job)

        output_video_path = settings.REELS_DIR / f"{project.id}.mp4"
        final_audio_duration = get_audio_duration(final_audio_path)

        _, scene_durations = render_reel_video(
            image_paths=image_paths,
            audio_path=final_audio_path,
            captions=captions,
            total_audio_duration=final_audio_duration,
            output_video_path=output_video_path,
            temp_dir=temp_dir,
        )

        # STEP 6: Thumbnail Generation
        thumbnail_path = settings.THUMBNAILS_DIR / f"{project.id}.jpg"
        generate_video_thumbnail(
            video_path=output_video_path,
            thumbnail_path=thumbnail_path,
            timestamp=min(1.0, final_audio_duration / 2),
        )

        # Clean up temporary video segments
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Update Project Scenes with durations and captions
        for idx, scene in enumerate(project.scenes):
            if idx < len(scene_durations):
                scene.duration_seconds = round(scene_durations[idx], 2)
            if idx < len(captions):
                scene.caption = captions[idx]

        project.status = JobStatus.COMPLETED
        project.duration_seconds = round(final_audio_duration, 2)
        project.video_filename = f"{project.id}.mp4"
        project.video_url = f"/media/reels/{project.id}.mp4"
        project.thumbnail_url = f"/media/thumbnails/{project.id}.jpg"
        db.save_project(project)

        # Mark Job Completed
        job.status = JobStatus.COMPLETED
        job.step = "Your Reel is ready 🎉"
        job.progress_percent = 100
        job.completed_at = now_iso()
        job.updated_at = now_iso()
        db.save_job(job)
        logger.info(f"Job {job_id} successfully completed for Project {project.id}!")

    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        job.status = JobStatus.FAILED
        job.step = "Render failed"
        job.error_message = str(e)
        job.updated_at = now_iso()
        db.save_job(job)

        project.status = JobStatus.FAILED
        db.save_project(project)
