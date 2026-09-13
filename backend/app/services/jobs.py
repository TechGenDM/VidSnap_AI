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

        # Ensure project script exists
        if not project.script or len(project.script.strip()) < 3:
            project.script = " ".join([s.narration or s.caption for s in project.scenes if (s.narration or s.caption)])

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

        # Respect explicit scene captions if already present (AI Story or user edit)
        existing_captions = [s.caption.strip() for s in project.scenes if s.caption and s.caption.strip()]
        if len(existing_captions) == len(image_paths):
            captions = existing_captions
        else:
            captions = split_script_into_captions(project.script, len(image_paths))
            for idx, c in enumerate(captions):
                if idx < len(project.scenes):
                    project.scenes[idx].caption = c

        # STEP 5: Visual Planning & RenderPlan Construction
        job.step = "Constructing cinematic render plan with camera motion"
        job.progress_percent = 75
        job.updated_at = now_iso()
        db.save_job(job)

        from app.services.visual_planning import VisualPlanningEngine
        from app.services.render_plan import RenderPlanBuilder
        from app.services.video import composite_render_plan, inspect_rendered_frames

        # Ensure visual plan and motions are populated on every scene
        for scene in project.scenes:
            if not scene.visual_plan:
                scene.visual_plan = VisualPlanningEngine.plan_scene_visuals(
                    scene=scene,
                    visual_style=project.style,
                )
            if not scene.motion:
                scene.motion = scene.visual_plan.motion
            if not scene.transition:
                scene.transition = scene.visual_plan.transition

        output_video_path = settings.REELS_DIR / f"{project.id}.mp4"
        final_audio_duration = get_audio_duration(final_audio_path)

        render_plan = RenderPlanBuilder.build_from_project(
            project=project,
            audio_path=final_audio_path,
            total_audio_duration=final_audio_duration,
            output_video_path=output_video_path,
            fps=settings.VIDEO_FPS,
        )

        # STEP 6: Video Rendering with Cinematic Motion & Transitions
        job.status = JobStatus.RENDERING
        job.step = "Compositing 1080x1920 Reel with cinematic motion & transitions"
        job.progress_percent = 85
        job.updated_at = now_iso()
        db.save_job(job)

        _, scene_durations = composite_render_plan(
            plan=render_plan,
            temp_dir=temp_dir,
        )

        # STEP 7: Quality Frame Inspection (15%, 50%, 85%)
        job.step = "Inspecting rendered frames for cinematic quality standards"
        job.progress_percent = 92
        job.updated_at = now_iso()
        db.save_job(job)

        inspection_dir = project_dir / "inspections"
        inspection_result = inspect_rendered_frames(
            video_path=output_video_path,
            output_dir=inspection_dir,
        )

        if not inspection_result.passed:
            critical_issues = "; ".join(inspection_result.issues)
            err_msg = f"Fatal render quality failure during frame inspection: {critical_issues}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        logger.info(
            f"Frame inspection passed successfully for {project.id}. "
            f"Resolution: {inspection_result.resolution}, Metrics: {inspection_result.metrics}"
        )

        # STEP 8: Thumbnail Generation
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
        project.render_history.append({
            "rendered_at": now_iso(),
            "duration_seconds": round(final_audio_duration, 2),
            "video_filename": f"{project.id}.mp4",
            "voice": project.voice,
            "music": project.music,
            "inspection": {
                "passed": inspection_result.passed,
                "resolution": inspection_result.resolution,
                "metrics": inspection_result.metrics,
            },
        })
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
