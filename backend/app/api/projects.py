import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from app.models import Project, Scene
from app.schemas import UpdateProjectScenes
from app.config import settings

router = APIRouter(prefix="/api/projects", tags=["projects"])

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
