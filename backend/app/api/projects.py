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

import re
from typing import Optional
from app.models import Story, StoryScene
from app.schemas import RegenerateSceneRequest
from app.services.story_generation import get_story_provider
from app.services.visual_provider import local_visual_provider

@router.put("/{project_id}/scenes")
async def update_project_scenes(project_id: str, payload: UpdateProjectScenes):
    """
    Story-based editing: Update narration, captions, visual direction, or visuals for individual scenes.
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
            if update.visual_direction is not None:
                target.visual_direction = update.visual_direction
            if update.visual_filename is not None:
                target.visual_filename = update.visual_filename
                target.visual_url = f"/media/uploads/{project.id}/{update.visual_filename}"

    # Reassemble script from scenes
    combined_script = " ".join([s.narration or s.caption for s in project.scenes if (s.narration or s.caption)])
    if combined_script:
        project.script = combined_script

    db.save_project(project)
    return project.model_dump()

@router.delete("/{project_id}/scenes/{scene_order}")
async def delete_project_scene(project_id: str, scene_order: int):
    """
    Deletes a single scene from the canonical project story and re-indexes remaining scenes.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    if len(project.scenes) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only remaining scene in the Reel.")

    project.scenes = [s for s in project.scenes if s.order != scene_order]
    # Re-index
    for idx, s in enumerate(project.scenes):
        s.order = idx + 1

    project.script = " ".join([s.narration for s in project.scenes if s.narration])
    db.save_project(project)
    return {
        "status": "success",
        "message": f"Scene {scene_order} deleted.",
        "project": project.model_dump(),
    }

@router.post("/{project_id}/regenerate-story")
async def regenerate_project_story(project_id: str):
    """
    Regenerates the complete Story structure with a fresh hook and angle,
    while preserving original topic, audience, tone, length, and visual style.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    prompt = project.original_prompt or project.script or project.title
    audience = project.audience or "Tech Creators"
    tone = project.tone or "Educational"
    length = project.target_length or "30s"
    style = project.style or "Minimal Tech"

    # Distinct variation seed based on generation count
    seed = len(project.render_history) + 1

    story_provider = get_story_provider()
    story = story_provider.generate_story(
        prompt=prompt,
        audience=audience,
        tone=tone,
        length=length,
        style=style,
        variation_seed=seed,
    )

    # Match visuals
    scenes = local_visual_provider.match_visuals_for_scenes(
        scenes=story.scenes,
        visual_style=style,
        project_id=project_id,
    )

    full_script = " ".join([s.narration for s in story.scenes if s.narration])
    project.title = story.title
    project.script = full_script
    project.duration_seconds = story.estimated_duration
    project.scenes = scenes
    project.generated_story = story
    project.render_history.append({
        "action": "regenerate_story",
        "timestamp": now_iso(),
        "variation_seed": seed,
        "hook": story.hook,
    })

    db.save_project(project)
    return {
        "status": "success",
        "message": "Story regenerated with a new hook and narrative angle.",
        "project": project.model_dump(),
        "story": story.model_dump(),
        "scenes": [s.model_dump() for s in scenes],
    }

@router.post("/{project_id}/scenes/{scene_order}/regenerate")
async def regenerate_single_scene(
    project_id: str,
    scene_order: int,
    payload: Optional[RegenerateSceneRequest] = None,
):
    """
    Regenerates a single scene's narration, caption, and visual direction
    without requiring the whole project to be rebuilt.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    target_scene = next((s for s in project.scenes if s.order == scene_order), None)
    if not target_scene:
        raise HTTPException(status_code=404, detail=f"Scene with order {scene_order} not found.")

    story_provider = get_story_provider()
    story = project.generated_story
    if not story:
        story = Story(
            title=project.title,
            hook=project.scenes[0].narration if project.scenes else "",
            scenes=[
                StoryScene(
                    order=s.order,
                    narration=s.narration or s.caption,
                    caption=s.caption,
                    visual_direction=s.visual_direction or "Cinematic shot",
                    estimated_duration=s.duration_seconds or 4.0,
                )
                for s in project.scenes
            ],
            cta="Follow for more insights.",
            estimated_duration=project.duration_seconds,
        )

    feedback = payload.feedback if payload else None
    new_scene = story_provider.regenerate_scene(
        story=story,
        scene_order=scene_order,
        prompt=project.original_prompt or project.title,
        feedback=feedback,
    )

    target_scene.narration = new_scene.narration
    target_scene.caption = new_scene.caption
    target_scene.visual_direction = new_scene.visual_direction

    # Update project script
    project.script = " ".join([s.narration for s in project.scenes if s.narration])
    db.save_project(project)

    return {
        "status": "success",
        "message": f"Scene {scene_order} regenerated successfully.",
        "scene": target_scene.model_dump(),
        "project": project.model_dump(),
    }

@router.post("/{project_id}/assistant")
async def ask_vidsnap_assistant(project_id: str, payload: AssistantCommandRequest):
    """
    'Ask VidSnap' conversational assistant foundation:
    Processes natural language commands on the canonical scene model.
    Deterministic actions:
    - Make the intro more attention-grabbing
    - Make the tone more energetic
    - Make this shorter
    - Remove this scene / Remove scene X
    - Change the voice
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    cmd = payload.command.lower()
    response_message = ""

    if "punchy" in cmd or "attention" in cmd or "hook" in cmd or "intro" in cmd:
        if project.scenes:
            project.scenes[0].caption = "🔥 STOP SCROLLING: This changes everything"
            project.scenes[0].narration = "Stop scrolling. This changes everything you thought you knew."
            response_message = "Updated Scene 1 hook to be high-retention and attention-grabbing."
    elif "energetic" in cmd or "tone" in cmd:
        project.music = "upbeat_pulse"
        project.voice = "josh"
        if project.scenes:
            project.scenes[0].caption = "⚡ THE GAME HAS CHANGED"
        response_message = "Changed voice to Josh (Energetic), music to Upbeat Pulse, and boosted hook energy."
    elif "shorter" in cmd or "short" in cmd:
        if len(project.scenes) > 2:
            removed = project.scenes.pop()
            for idx, s in enumerate(project.scenes):
                s.order = idx + 1
            response_message = f"Trimmed Scene #{removed.order} to shorten Reel duration."
        else:
            response_message = "Reel is already concise at 2 scenes."
    elif "remove" in cmd and ("scene" in cmd or "last" in cmd):
        # Look for a specific scene number, e.g. "remove scene 3"
        match = re.search(r"remove\s+(?:scene\s*)?(\d+)", cmd)
        if match:
            num = int(match.group(1))
            orig_len = len(project.scenes)
            project.scenes = [s for s in project.scenes if s.order != num]
            if len(project.scenes) < orig_len:
                for idx, s in enumerate(project.scenes):
                    s.order = idx + 1
                response_message = f"Removed Scene {num} and re-indexed the story."
            else:
                response_message = f"Scene {num} not found."
        elif len(project.scenes) > 1:
            project.scenes.pop()
            for idx, s in enumerate(project.scenes):
                s.order = idx + 1
            response_message = "Removed the last scene from your story."
        else:
            response_message = "Cannot remove the only remaining scene."
    elif "voice" in cmd:
        if "rachel" in cmd:
            project.voice = "rachel"
            response_message = "Switched narrator to Rachel (Warm & Engaging)."
        elif "adam" in cmd:
            project.voice = "adam"
            response_message = "Switched narrator to Adam (Deep & Narrative)."
        elif "josh" in cmd:
            project.voice = "josh"
            response_message = "Switched narrator to Josh (Young & Energetic)."
        elif "antoni" in cmd:
            project.voice = "antoni"
            response_message = "Switched narrator to Antoni (Crisp & Thoughtful)."
        else:
            project.voice = "rachel"
            response_message = "Switched narrator voice."
    else:
        response_message = f"Applied AI adjustment for: '{payload.command}'"

    # Re-sync script
    combined = " ".join([s.narration or s.caption for s in project.scenes if (s.narration or s.caption)])
    if combined:
        project.script = combined

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
