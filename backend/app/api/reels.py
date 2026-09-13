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

@router.post("/ai")
async def create_ai_reel(payload: AIReelCreate):
    """
    AI Reel Foundation endpoint:
    Accepts idea prompt and configuration, generates story scenes & script breakdown.
    """
    project_id = str(uuid.uuid4())
    now = now_iso()

    # Formulate structured script and hook based on user prompt
    hook = f"Here is why {payload.prompt.strip().rstrip('.')} matters right now."
    body = f"When we look closer at {payload.prompt.strip()}, the underlying shift becomes undeniable. Everything is moving towards autonomous workflows."
    cta = "Follow for more daily breakthroughs."
    generated_script = f"{hook} {body} {cta}"

    project = Project(
        id=project_id,
        title=payload.prompt[:35] + ("..." if len(payload.prompt) > 35 else ""),
        created_at=now,
        status=JobStatus.QUEUED,
        duration_seconds=0.0,
        voice=payload.voice,
        music="upbeat_pulse",
        style=payload.visual_style,
        script=generated_script,
        scenes=[
            Scene(
                id="scene_1",
                order=1,
                visual_filename="placeholder_1.jpg",
                visual_url="/media/templates/1.jpg",
                narration=hook,
                caption=hook,
                duration_seconds=3.0,
            ),
            Scene(
                id="scene_2",
                order=2,
                visual_filename="placeholder_2.jpg",
                visual_url="/media/templates/2.jpg",
                narration=body,
                caption=body,
                duration_seconds=5.0,
            ),
            Scene(
                id="scene_3",
                order=3,
                visual_filename="placeholder_3.jpg",
                visual_url="/media/templates/3.jpg",
                narration=cta,
                caption=cta,
                duration_seconds=3.0,
            ),
        ],
        mode="ai",
    )
    db.save_project(project)

    return {
        "project_id": project_id,
        "status": "planned",
        "script": generated_script,
        "scenes": [s.model_dump() for s in project.scenes],
        "message": "AI Story planned. Connect visuals or approve script to render.",
    }
