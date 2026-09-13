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
