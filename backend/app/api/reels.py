import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from app.models import Project, Job, JobStatus, Scene
from app.database import db
from app.services.storage import save_uploaded_image
from app.services.jobs import process_quick_reel_job
from app.schemas import AIReelCreate

router = APIRouter(prefix="/api/reels", tags=["reels"])
logger = logging.getLogger("vidsnap.api.reels")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.post("/quick")
async def create_quick_reel(
    background_tasks: BackgroundTasks,
    script: str = Form(..., min_length=3, max_length=5000),
    voice: str = Form("adam"),
    music: Optional[str] = Form("ambient_chill"),
    style: str = Form("cinematic"),
    image_order: Optional[str] = Form(None), # JSON list of indices or original names
    images: list[UploadFile] = File(...),
):
    """
    Creates a Quick Reel from uploaded images and script.
    Enqueues the rendering job in the background and returns job ID.
    """
    if not images or len(images) == 0:
        raise HTTPException(status_code=400, detail="At least one image is required.")

    if len(images) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 images allowed per reel.")

    project_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    now = now_iso()

    # Save uploaded images safely
    saved_scenes: list[Scene] = []
    saved_filenames: list[str] = []

    for idx, upload_file in enumerate(images):
        safe_name, _ = await save_uploaded_image(project_id, upload_file)
        saved_filenames.append(safe_name)

    # Reorder images if client specified custom order
    ordered_filenames = saved_filenames
    if image_order:
        try:
            order_indices = json.loads(image_order)
            if isinstance(order_indices, list) and len(order_indices) == len(saved_filenames):
                ordered_filenames = [saved_filenames[i] for i in order_indices if 0 <= i < len(saved_filenames)]
        except Exception as e:
            logger.warning(f"Could not parse image_order '{image_order}': {e}. Preserving original order.")

    for idx, fname in enumerate(ordered_filenames):
        saved_scenes.append(
            Scene(
                id=f"scene_{idx + 1}",
                order=idx + 1,
                visual_filename=fname,
                visual_url=f"/media/uploads/{project_id}/{fname}",
                narration="",
                caption="",
                duration_seconds=0.0,
            )
        )

    # Derive clean title from first few words of script
    words = script.strip().split()
    title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
    if not title:
        title = "Quick Reel"

    project = Project(
        id=project_id,
        title=title,
        created_at=now,
        status=JobStatus.QUEUED,
        duration_seconds=0.0,
        voice=voice,
        music=music,
        style=style,
        script=script.strip(),
        scenes=saved_scenes,
        mode="quick",
    )
    db.save_project(project)

    job = Job(
        id=job_id,
        project_id=project_id,
        status=JobStatus.QUEUED,
        step="Job enqueued in render pipeline",
        progress_percent=5,
        created_at=now,
        updated_at=now,
    )
    db.save_job(job)

    # Launch background rendering pipeline
    background_tasks.add_task(process_quick_reel_job, job_id)

    return {
        "project_id": project_id,
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "message": "Quick Reel job enqueued successfully.",
    }

from app.services.story_generation import get_story_provider
from app.services.visual_provider import local_visual_provider

@router.post("/ai")
async def create_ai_reel(payload: AIReelCreate):
    """
    AI Reel Creation endpoint:
    Accepts idea prompt and parameters, produces structured Story, matches local visuals,
    and returns canonical project state for human review without auto-rendering.
    """
    project_id = str(uuid.uuid4())
    now = now_iso()

    # 1. Generate structured story via provider
    story_provider = get_story_provider()
    story = story_provider.generate_story(
        prompt=payload.prompt,
        audience=payload.audience,
        tone=payload.tone,
        length=payload.length,
        style=payload.visual_style,
        variation_seed=0,
    )

    # 2. Match visuals via LocalAssetProvider
    scenes = local_visual_provider.match_visuals_for_scenes(
        scenes=story.scenes,
        visual_style=payload.visual_style,
        project_id=project_id,
    )

    # 3. Formulate narration script from scenes
    full_script = " ".join([s.narration for s in story.scenes if s.narration])

    # 4. Save canonical Project
    project = Project(
        id=project_id,
        title=story.title,
        created_at=now,
        status=JobStatus.QUEUED,
        duration_seconds=story.estimated_duration,
        voice=payload.voice,
        music=payload.music or "ambient_chill",
        style=payload.visual_style,
        script=full_script,
        scenes=scenes,
        mode="ai",
        source_type="ai",
        original_prompt=payload.prompt,
        audience=payload.audience,
        tone=payload.tone,
        target_length=payload.length,
        generated_story=story,
        render_history=[],
    )
    db.save_project(project)

    return {
        "project_id": project_id,
        "status": "planned",
        "story": story.model_dump(),
        "scenes": [s.model_dump() for s in project.scenes],
        "script": full_script,
        "message": "AI Story generated successfully. Review and edit before rendering.",
    }
