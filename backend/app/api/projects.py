import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.database import db
from app.models import Project, Scene, Job, JobStatus
from app.schemas import UpdateProjectScenes
from app.config import settings
from app.services.jobs import process_quick_reel_job

router = APIRouter(prefix="/api/projects", tags=["projects"])

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class AssistantCommandRequest(BaseModel):
    command: str

@router.get("")
async def list_projects():
    """
    Returns list of all projects sorted by creation date descending.
    """
    projects = db.list_projects()
    return [p.model_dump() for p in projects]

@router.get("/{project_id}")
async def get_project(project_id: str):
    """
    Returns a single project with its scenes and metadata.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return project.model_dump()

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    Deletes a project and its media files.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    # Remove video file if exists
    if project.video_filename:
        video_path = settings.REELS_DIR / project.video_filename
        video_path.unlink(missing_ok=True)

    thumbnail_path = settings.THUMBNAILS_DIR / f"{project.id}.jpg"
    thumbnail_path.unlink(missing_ok=True)

    db.delete_project(project_id)
    return {"status": "success", "message": f"Project {project_id} deleted."}

@router.put("/{project_id}/scenes")
async def update_project_scenes(project_id: str, payload: UpdateProjectScenes):
    """
    Story-based editing: Update narration, captions, or visuals for individual scenes.
    VidSnap edits the story, not the timeline!
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    scene_map = {s.id: s for s in project.scenes}
    for update in payload.scenes:
        if update.id in scene_map:
            target = scene_map[update.id]
            if update.narration is not None:
                target.narration = update.narration
            if update.caption is not None:
                target.caption = update.caption
            if update.visual_filename is not None:
                target.visual_filename = update.visual_filename
                target.visual_url = f"/media/uploads/{project.id}/{update.visual_filename}"

    # Reassemble script from scenes
    combined_script = " ".join([s.narration or s.caption for s in project.scenes if (s.narration or s.caption)])
    if combined_script:
        project.script = combined_script

    db.save_project(project)
    return project.model_dump()

@router.post("/{project_id}/assistant")
async def ask_vidsnap_assistant(project_id: str, payload: AssistantCommandRequest):
    """
    'Ask VidSnap' conversational assistant foundation:
    Processes natural language commands on the story (e.g. 'Make the intro more punchy').
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    cmd = payload.command.lower()
    response_message = ""

    if "punchy" in cmd or "attention" in cmd or "hook" in cmd:
        if project.scenes:
            project.scenes[0].caption = "🔥 STOP SCROLLING: This changes everything."
            project.scenes[0].narration = "Stop scrolling. This changes everything you thought you knew."
            response_message = "Updated Scene 1 hook to be high-retention and punchy."
    elif "energetic" in cmd or "tone" in cmd:
        project.music = "upbeat_pulse"
        project.voice = "josh"
        response_message = "Changed voice to Josh (Energetic) and music to Upbeat Pulse."
    elif "voice" in cmd:
        if "rachel" in cmd:
            project.voice = "rachel"
            response_message = "Switched narrator to Rachel."
        elif "adam" in cmd:
            project.voice = "adam"
            response_message = "Switched narrator to Adam."
        else:
            project.voice = "rachel"
            response_message = "Switched narrator voice."
    else:
        response_message = f"Applied AI adjustment for: '{payload.command}'"

    db.save_project(project)
    return {
        "status": "success",
        "action": response_message,
        "project": project.model_dump(),
    }

@router.post("/{project_id}/render")
async def render_project(project_id: str, background_tasks: BackgroundTasks):
    """
    Triggers 1080x1920 video rendering for an existing story project.
    Allows creators to re-render after editing text, captions, or voices.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    if not project.scenes or len(project.scenes) == 0:
        raise HTTPException(status_code=400, detail="Cannot render a project with zero scenes.")

    job_id = str(uuid.uuid4())
    now = now_iso()

    job = Job(
        id=job_id,
        project_id=project_id,
        status=JobStatus.QUEUED,
        step="Render re-enqueued for edited story",
        progress_percent=5,
        created_at=now,
        updated_at=now,
    )
    db.save_job(job)

    # Launch rendering pipeline in background
    background_tasks.add_task(process_quick_reel_job, job_id)

    return {
        "project_id": project_id,
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "message": "Reel rendering enqueued successfully.",
    }
