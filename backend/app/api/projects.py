import os
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from pydantic import BaseModel
from app.database import db
from app.models import Project, Scene, Job, JobStatus, LifecycleState
from app.schemas import UpdateProjectScenes, SelectVisualRequest, QualityGateResponse
from app.config import settings
from app.services.jobs import process_quick_reel_job
from app.services.storage import save_uploaded_image
from app.services.quality_gate import QualityGateService

router = APIRouter(prefix="/api/projects", tags=["projects"])

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class AssistantCommandRequest(BaseModel):
    command: Optional[str] = None
    message: Optional[str] = None

    def get_command_text(self) -> str:
        return (self.command or self.message or "").strip()

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
from app.schemas import RegenerateSceneRequest, RegenerateVisualRequest, ApplyHookRequest
from app.services.story_generation import get_story_provider
from app.services.visual_provider import local_visual_provider, smart_visual_provider
from app.services.creator_presets import evaluate_story_qualitative, generate_alternative_hooks

@router.put("/{project_id}/scenes")
async def update_project_scenes(project_id: str, payload: UpdateProjectScenes):
    """
    Story-based editing: Update narration, captions, visual direction, motion,
    transition, duration, or visual asset for individual scenes.
    VidSnap edits the story, not the timeline!
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    # Snapshot current state before editing
    project.create_snapshot("Edited scenes")

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
            if update.visual_url is not None:
                target.visual_url = update.visual_url
            elif update.visual_filename is not None:
                target.visual_url = f"/media/uploads/{project.id}/{update.visual_filename}"
            if update.scene_role is not None:
                target.scene_role = update.scene_role
            if update.motion is not None:
                target.motion = update.motion
                if target.visual_plan:
                    target.visual_plan.motion = update.motion
            if update.transition is not None:
                target.transition = update.transition
                if target.visual_plan:
                    target.visual_plan.transition = update.transition
            if update.duration_seconds is not None and update.duration_seconds > 0:
                target.duration_seconds = update.duration_seconds
            if update.visual_prompt is not None and target.visual_plan:
                target.visual_plan.description = update.visual_prompt
            if update.visual_source is not None:
                target.visual_source = update.visual_source

    # Reassemble script from scenes
    combined_script = " ".join([s.narration or s.caption for s in project.scenes if (s.narration or s.caption)])
    if combined_script:
        project.script = combined_script

    project.metrics.has_edited_scene = True
    db.save_project(project)
    return project.model_dump()

@router.post("/{project_id}/scenes/{scene_order}/upload-asset")
async def upload_scene_custom_asset(
    project_id: str,
    scene_order: int,
    file: UploadFile = File(...),
):
    """
    Uploads a custom image or video B-roll asset for a specific scene.
    Replaces AI visual with the custom asset and marks it as canonical.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    target_scene = next((s for s in project.scenes if s.order == scene_order), None)
    if not target_scene:
        raise HTTPException(status_code=404, detail=f"Scene with order {scene_order} not found.")

    safe_name, saved_path = await save_uploaded_image(project_id, file)
    target_scene.visual_filename = safe_name
    target_scene.visual_url = f"/media/uploads/{project.id}/{safe_name}"
    target_scene.visual_source = "custom"
    if target_scene.visual_plan:
        target_scene.visual_plan.visual_type = "custom_broll"
        target_scene.visual_plan.subject = f"custom upload ({file.filename})"

    project.create_snapshot(f"Uploaded custom B-Roll for Scene {scene_order}")
    db.save_project(project)

    return {
        "status": "success",
        "message": f"Custom asset '{safe_name}' uploaded for Scene {scene_order}.",
        "scene": target_scene.model_dump(),
        "project": project.model_dump(),
    }

@router.get("/{project_id}/scenes/{scene_order}/visual-alternatives")
async def get_scene_visual_alternatives(project_id: str, scene_order: int):
    """
    Returns candidate visual alternatives (stock templates, previous AI assets, domain assets)
    that a creator can choose from for Scene N.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    target_scene = next((s for s in project.scenes if s.order == scene_order), None)
    if not target_scene:
        raise HTTPException(status_code=404, detail=f"Scene with order {scene_order} not found.")

    alternatives = [
        {
            "filename": "1.jpg",
            "url": "/media/templates/1.jpg",
            "label": "Minimal Tech Desk",
            "type": "stock",
            "domain": "technology",
        },
        {
            "filename": "2.jpg",
            "url": "/media/templates/2.jpg",
            "label": "Connected Network Graph",
            "type": "stock",
            "domain": "technology",
        },
        {
            "filename": "3.jpg",
            "url": "/media/templates/3.jpg",
            "label": "Atmospheric Daylight Horizon",
            "type": "stock",
            "domain": "personal",
        },
        {
            "filename": "4.jpg",
            "url": "/media/templates/4.jpg",
            "label": "High-Contrast Metrics & Growth",
            "type": "stock",
            "domain": "business",
        },
        {
            "filename": "5.jpg",
            "url": "/media/templates/5.jpg",
            "label": "Modern Architecture Studio",
            "type": "stock",
            "domain": "education",
        },
    ]

    project_dir = settings.UPLOADS_DIR / project_id
    if project_dir.exists():
        for f in project_dir.iterdir():
            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"] and f.name != target_scene.visual_filename:
                alternatives.append({
                    "filename": f.name,
                    "url": f"/media/uploads/{project_id}/{f.name}",
                    "label": f"Project Asset: {f.stem}",
                    "type": "project_upload",
                    "domain": "custom",
                })

    return {
        "status": "success",
        "scene_order": scene_order,
        "current_visual": target_scene.visual_filename,
        "alternatives": alternatives,
    }

@router.post("/{project_id}/scenes/{scene_order}/select-visual")
async def select_scene_visual(
    project_id: str,
    scene_order: int,
    payload: SelectVisualRequest,
):
    """
    Sets a chosen alternative asset as canonical for Scene N.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    target_scene = next((s for s in project.scenes if s.order == scene_order), None)
    if not target_scene:
        raise HTTPException(status_code=404, detail=f"Scene with order {scene_order} not found.")

    target_scene.visual_filename = payload.visual_filename
    target_scene.visual_url = payload.visual_url
    target_scene.visual_source = payload.visual_type or "custom_selected"

    project.metrics.has_edited_scene = True
    project.create_snapshot(f"Selected visual '{payload.visual_filename}' for Scene {scene_order}")
    db.save_project(project)

    return {
        "status": "success",
        "message": f"Visual for Scene {scene_order} set to '{payload.visual_filename}'.",
        "scene": target_scene.model_dump(),
        "project": project.model_dump(),
    }

@router.delete("/{project_id}/scenes/{scene_order}/visual")
async def remove_scene_visual(project_id: str, scene_order: int):
    """
    Removes custom visual on Scene N and gracefully falls back to stock/default asset.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    target_scene = next((s for s in project.scenes if s.order == scene_order), None)
    if not target_scene:
        raise HTTPException(status_code=404, detail=f"Scene with order {scene_order} not found.")

    fallback_file = f"{((scene_order - 1) % 5) + 1}.jpg"
    target_scene.visual_filename = fallback_file
    target_scene.visual_url = f"/media/templates/{fallback_file}"
    target_scene.visual_source = "stock_fallback"

    project.create_snapshot(f"Reset visual for Scene {scene_order} to stock fallback")
    db.save_project(project)

    return {
        "status": "success",
        "message": f"Custom visual removed for Scene {scene_order}. Reverted to stock fallback.",
        "scene": target_scene.model_dump(),
        "project": project.model_dump(),
    }

@router.get("/{project_id}/quality-gate")
async def get_project_quality_gate(project_id: str):
    """
    Runs or returns the final quality gate report for the project.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    video_path = settings.REELS_DIR / f"{project.id}.mp4"
    if not video_path.exists():
        return {
            "passed": False,
            "is_ready_to_post": False,
            "status_label": "Not Rendered",
            "blocking_errors": ["Video has not been rendered yet."],
            "actionable_warnings": [],
            "checks": {"file_exists": False},
        }

    report = QualityGateService.validate_reel(project, video_path)
    return report.model_dump()

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

    # Match visuals with structured visual intelligence
    scenes = local_visual_provider.match_visuals_for_scenes(
        scenes=story.scenes,
        visual_style=style,
        project_id=project_id,
        domain=story.domain or "technology",
        tone=tone,
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

    project.create_snapshot(f"Pre-regenerate Scene {scene_order}")

    target_scene.narration = new_scene.narration
    target_scene.caption = new_scene.caption
    target_scene.visual_direction = new_scene.visual_direction

    # Update project script
    project.script = " ".join([s.narration for s in project.scenes if s.narration])
    project.create_snapshot(f"Regenerated Scene {scene_order}")
    db.save_project(project)

    return {
        "status": "success",
        "message": f"Scene {scene_order} regenerated successfully.",
        "scene": target_scene.model_dump(),
        "project": project.model_dump(),
    }

@router.post("/{project_id}/scenes/{scene_order}/regenerate-visual")
async def regenerate_single_scene_visual(
    project_id: str,
    scene_order: int,
    payload: Optional[RegenerateVisualRequest] = None,
):
    """
    Regenerates ONLY a single scene's visual asset.
    Preserves narration, captions, scene order, and unrelated project state.
    Supports AI generation with fallback to stock library.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    target_scene = next((s for s in project.scenes if s.order == scene_order), None)
    if not target_scene:
        raise HTTPException(status_code=404, detail=f"Scene with order {scene_order} not found.")

    project.create_snapshot(f"Pre-regenerate visual for Scene {scene_order}")

    custom_prompt = payload.prompt if payload else None
    seed = payload.seed if payload else None

    updated_scene, diag = smart_visual_provider.regenerate_single_scene_visual(
        scene=target_scene,
        visual_style=project.style,
        project_id=project.id,
        custom_prompt=custom_prompt,
        seed=seed,
    )

    # Record diagnostic in project history
    if not hasattr(project, "generation_diagnostics") or project.generation_diagnostics is None:
        project.generation_diagnostics = []
    project.generation_diagnostics.append(diag)

    project.create_snapshot(f"Regenerated visual for Scene {scene_order}")
    db.save_project(project)

    return {
        "status": "success",
        "scene_order": scene_order,
        "message": f"Visual for scene {scene_order} regenerated successfully.",
        "scene": updated_scene.model_dump(),
        "project": project.model_dump(),
        "diagnostic": diag,
    }

@router.post("/{project_id}/duplicate")
async def duplicate_project(project_id: str):
    """
    Creates an independent duplicate of the project.
    Assigns a new project ID, deep-copies all scenes and story data,
    and initializes an independent version history so modifications to the duplicate
    never mutate the original project.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    new_id = str(uuid.uuid4())
    now = now_iso()

    copied_scenes = [Scene.model_validate(s.model_dump()) for s in project.scenes]
    copied_story = (
        Story.model_validate(project.generated_story.model_dump())
        if project.generated_story
        else None
    )

    new_project = Project(
        id=new_id,
        title=f"{project.title} (Variant)",
        created_at=now,
        status=JobStatus.QUEUED,
        lifecycle_state=LifecycleState.STORY_READY if project.scenes else LifecycleState.DRAFT,
        video_url=None,
        duration_seconds=project.duration_seconds,
        voice=project.voice,
        music=project.music,
        style=project.style,
        script=project.script,
        scenes=copied_scenes,
        mode=project.mode,
        source_type=project.source_type,
        visual_source=project.visual_source,
        active_preset=project.active_preset,
        original_prompt=project.original_prompt,
        audience=project.audience,
        tone=project.tone,
        target_length=project.target_length,
        generated_story=copied_story,
        qualitative_feedback=list(project.qualitative_feedback),
        versions=[],
        metrics=project.metrics.model_copy() if hasattr(project, "metrics") and project.metrics else None,
    )
    if new_project.metrics:
        new_project.metrics.has_duplicated = True
    # Independent version history snapshot
    new_project.create_snapshot(f"Initial Version (Duplicated from {project.id[:8]})")
    db.save_project(new_project)

    return new_project.model_dump()

@router.get("/{project_id}/versions")
async def get_project_versions(project_id: str):
    """
    Returns complete immutable version history snapshots for the project.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return [v.model_dump() for v in project.versions]

@router.post("/{project_id}/versions/{version_number}/restore")
async def restore_project_version(project_id: str, version_number: int):
    """
    Restores the project state from an immutable historical snapshot.
    Preserves historical records and records a new snapshot representing the restore event.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    try:
        restore_snapshot = project.restore_version(version_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if project.metrics:
        project.metrics.has_regenerated_version = True
    db.save_project(project)
    return {
        "status": "success",
        "success": True,
        "message": f"Successfully restored Version {version_number}.",
        "restored_version": restore_snapshot.model_dump(),
        "project": project.model_dump(),
    }

@router.get("/{project_id}/alternatives/hook")
async def get_hook_alternatives(project_id: str):
    """
    Generates 2 distinct strategic hook alternatives faithful to the project's topic and domain.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    topic = project.original_prompt or project.title or "technology"
    current_hook = (
        project.generated_story.hook
        if project.generated_story
        else (project.scenes[0].narration if project.scenes else "")
    )
    domain = getattr(project.generated_story, "domain", "technology") or "technology"

    alternatives = generate_alternative_hooks(topic=topic, current_hook=current_hook, domain=domain)
    return {
        "status": "success",
        "topic": topic,
        "current_hook": current_hook,
        "alternatives": alternatives,
    }

@router.post("/{project_id}/apply-hook")
async def apply_hook_alternative(project_id: str, payload: ApplyHookRequest):
    """
    Applies an alternative hook:
    Takes an immutable snapshot first, updates Scene 1 narration & caption,
    updates canonical story, and preserves remaining scenes.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    if not project.scenes:
        raise HTTPException(status_code=400, detail="Project has no scenes to apply hook to.")

    # Snapshot prior state
    project.create_snapshot("Pre-hook update snapshot")

    # Apply hook
    project.scenes[0].narration = payload.hook
    if payload.caption:
        project.scenes[0].caption = payload.caption
    if project.generated_story:
        project.generated_story.hook = payload.hook

    project.script = " ".join([s.narration for s in project.scenes if s.narration])
    if project.generated_story:
        project.qualitative_feedback = evaluate_story_qualitative(project.generated_story, project.scenes)

    if project.metrics:
        project.metrics.has_edited_scene = True
    project.create_snapshot(f"Applied Alternative Hook: '{payload.hook[:30]}...'")
    db.save_project(project)
    return {
        "status": "success",
        "success": True,
        "message": "Alternative hook applied successfully.",
        "project": project.model_dump(),
    }

@router.post("/{project_id}/assistant")
async def ask_vidsnap_assistant(project_id: str, payload: AssistantCommandRequest):
    """
    Deterministic & Explainable 'Ask VidSnap' assistant:
    Executes safe, explicit creative operations on canonical Story/project state.
    Takes an immutable snapshot before every successful modification.
    Returns honest explanation for unsupported commands without mutating state.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    raw_cmd = payload.get_command_text()
    cmd = raw_cmd.lower()
    success = False
    change_summary = ""

    from app.services.creative_engine import TopicInterpreter
    interp = TopicInterpreter.interpret(project.original_prompt or project.title or "technology")

    # 1. Make the hook stronger / punchy / attention-grabbing intro
    if "hook" in cmd or "intro" in cmd or "attention" in cmd or "punchy" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        alt_hook = interp.hook_angles.get("problem", f"The single biggest bottleneck in {interp.topic} isn't what you think.")
        if project.scenes:
            project.scenes[0].narration = alt_hook
            project.scenes[0].caption = "STOP SCROLLING: THE REAL BOTTLENECK"
        if project.generated_story:
            project.generated_story.hook = alt_hook
        change_summary = f"Refined Scene 1 hook to focus on acute curiosity: '{alt_hook}'"
        success = True

    # 2. Make this more provocative
    elif "provocative" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        prov_hook = f"Everything you have been told about {interp.topic} is dangerously outdated."
        if project.scenes:
            project.scenes[0].narration = prov_hook
            project.scenes[0].caption = "UNCOMFORTABLE TRUTH"
        if project.generated_story:
            project.generated_story.hook = prov_hook
        change_summary = f"Updated hook to a bold provocative angle: '{prov_hook}'"
        success = True

    # 3. Make this 20 seconds / Make this N seconds / Make this shorter
    elif "20 second" in cmd or "20s" in cmd or "shorter" in cmd or "short" in cmd or re.search(r"(\d+)\s*(?:seconds?|s)\b", cmd):
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        target_match = re.search(r"(\d+)\s*(?:seconds?|s)\b", cmd)
        
        # When shortening, remove a scene if more than 2 scenes exist
        if len(project.scenes) > 2:
            project.scenes.pop()
            for idx, s in enumerate(project.scenes):
                s.order = idx + 1

        if target_match:
            target_secs = float(target_match.group(1))
            per_scene = round(target_secs / max(1, len(project.scenes)), 1)
            for s in project.scenes:
                words = s.narration.split()
                if len(words) > 10:
                    s.narration = " ".join(words[:10]).rstrip(",;:") + "."
                s.duration_seconds = per_scene
        else:
            for s in project.scenes:
                words = s.narration.split()
                if len(words) > 12:
                    s.narration = " ".join(words[:12]).rstrip(",;:") + "."
                s.duration_seconds = max(2.5, round(s.duration_seconds * 0.75, 1))

        project.duration_seconds = sum(s.duration_seconds for s in project.scenes)
        if project.generated_story:
            project.generated_story.estimated_duration = project.duration_seconds
        change_summary = f"Compressed scene narrations and tightened Reel duration to {round(project.duration_seconds, 1)}s."
        success = True

    # 4. Make this more technical
    elif "technical" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        if interp.domain == "technology":
            for s in project.scenes:
                if s.scene_role == "insight" or s.order == 2:
                    s.narration = f"By offloading AST syntax parsing and deterministic testing, {interp.topic} lets engineers focus purely on architecture and state constraints."
                    s.caption = "AST AND STATE LOGIC"
                elif s.order == 3:
                    s.narration = "Developers transition into system orchestrators, verifying automated pull requests and container deployment health."
                    s.caption = "SYSTEM ORCHESTRATION"
            change_summary = "Enhanced technical specificity with architecture and state constraints."
        elif interp.domain == "science":
            for s in project.scenes:
                if s.scene_role == "insight" or s.order == 2:
                    s.narration = "Rayleigh scattering intensity is inversely proportional to the fourth power of the light's wavelength."
                    s.caption = "RAYLEIGH SCATTERING LAW"
            change_summary = "Added physical wavelength scattering equations and scientific rigor."
        else:
            for s in project.scenes:
                if s.scene_role == "insight" or s.order == 2:
                    s.narration = f"Quantitative cohort retention and unit economics validate {interp.topic} far faster than speculative roadmaps."
                    s.caption = "COHORT RETENTION METRICS"
            change_summary = "Injected quantitative validation and unit economics metrics."
        success = True

    # 5. Make it sound more conversational / conversational
    elif "conversational" in cmd or "sound conversational" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        if project.scenes:
            project.scenes[0].narration = f"Here is the thing about {interp.topic} that nobody really talks about."
            project.scenes[0].caption = "LET'S BE HONEST"
        if len(project.scenes) > 1:
            project.scenes[1].narration = f"Most people overcomplicate {interp.topic}, but once you see the pattern, everything clicks."
            project.scenes[1].caption = "THE SIMPLE PATTERN"
        change_summary = "Shifted narration into a warm, conversational, first-person style."
        success = True

    # 6. Use simpler language / simple language
    elif "simpler language" in cmd or "simple language" in cmd or "simpler" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        for s in project.scenes:
            s.narration = (
                s.narration.replace("bottleneck", "problem")
                .replace("deterministic", "reliable")
                .replace("architecture", "design")
                .replace("orchestrators", "directors")
                .replace("quantitative", "direct")
                .replace("paradigm", "approach")
                .replace("accelerate", "speed up")
            )
            s.caption = (
                s.caption.replace("BOTTLENECK", "PROBLEM")
                .replace("DETERMINISTIC", "RELIABLE")
                .replace("ORCHESTRATION", "TEAMWORK")
            )
        change_summary = "Simplified phrasing and vocabulary across all scenes for broad clarity."
        success = True

    # 7. Replace scene N
    elif "replace scene" in cmd or (re.search(r"replace\s+(?:scene\s*)?(\d+)", cmd)):
        match = re.search(r"replace\s+(?:scene\s*)?(\d+)", cmd)
        if match:
            scene_num = int(match.group(1))
            target_scene = next((s for s in project.scenes if s.order == scene_num), None)
            if target_scene:
                project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
                target_scene.narration = f"Here is another angle on {interp.topic} that most creators overlook."
                target_scene.caption = "ANOTHER PERSPECTIVE"
                target_scene.visual_direction = f"Engaging focal visual illustrating practical {interp.topic}"
                change_summary = f"Replaced Scene {scene_num} with a fresh perspective and clear caption."
                success = True
            else:
                change_summary = f"Scene {scene_num} does not exist in this project."
                success = False
        else:
            change_summary = "Please specify the scene number to replace (e.g. 'Replace scene 2')."
            success = False

    # 8. Change the visual for scene N
    elif "visual for scene" in cmd or re.search(r"visual\s+(?:for\s+)?(?:scene\s*)?(\d+)", cmd):
        match = re.search(r"visual\s+(?:for\s+)?(?:scene\s*)?(\d+)", cmd)
        if match:
            scene_num = int(match.group(1))
            target_scene = next((s for s in project.scenes if s.order == scene_num), None)
            if target_scene:
                project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
                updated_scene, diag = smart_visual_provider.regenerate_single_scene_visual(
                    scene=target_scene,
                    visual_style=project.style,
                    project_id=project.id,
                )
                change_summary = f"Updated visual asset for Scene {scene_num}."
                success = True
            else:
                change_summary = f"Scene {scene_num} does not exist in this project."
                success = False
        else:
            change_summary = "Please specify which scene's visual to change (e.g. 'Change visual for scene 2')."
            success = False

    # 9. Give me a stronger ending
    elif "stronger ending" in cmd or "strong ending" in cmd or "better ending" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        if project.scenes:
            last_scene = project.scenes[-1]
            last_scene.narration = f"The question isn't whether {interp.topic} will change your workflow. It's whether you'll lead it or catch up. Start building now."
            last_scene.caption = "START BUILDING NOW"
        if project.generated_story:
            project.generated_story.cta = "Start building now."
        change_summary = "Replaced ending with a high-impact call to action and clear payoff."
        success = True

    # 10. Remove unnecessary repetition
    elif "repetition" in cmd or "repeated" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        seen_words = set()
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "it", "this", "that"}
        for s in project.scenes:
            words = s.narration.split()
            cleaned_words = []
            for w in words:
                low_w = w.lower().strip(",.?!")
                if low_w in seen_words and low_w not in stopwords and len(low_w) > 4:
                    cleaned_words.append("it")
                else:
                    cleaned_words.append(w)
                    if low_w not in stopwords and len(low_w) > 4:
                        seen_words.add(low_w)
            s.narration = " ".join(cleaned_words)
        change_summary = "Removed repeated keywords and phrases across consecutive scenes."
        success = True

    # 11. Energy / Voice controls
    elif "energetic" in cmd or "energy" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        project.music = "upbeat_pulse"
        project.voice = "josh"
        if project.scenes:
            project.scenes[0].narration = f"Here is what completely transforms {interp.topic} today—and why you cannot afford to ignore it."
            project.scenes[0].caption = "TRANSFORM YOUR WORKFLOW"
        change_summary = "Switched voice to Josh (Energetic), set music to Upbeat Pulse, and energized narration."
        success = True

    elif "voice" in cmd:
        project.create_snapshot(f"Ask VidSnap: '{raw_cmd}'")
        if "rachel" in cmd:
            project.voice = "rachel"
            change_summary = "Switched narrator to Rachel (Warm & Engaging)."
        elif "adam" in cmd:
            project.voice = "adam"
            change_summary = "Switched narrator to Adam (Deep & Narrative)."
        elif "josh" in cmd:
            project.voice = "josh"
            change_summary = "Switched narrator to Josh (Young & Energetic)."
        elif "antoni" in cmd:
            project.voice = "antoni"
            change_summary = "Switched narrator to Antoni (Crisp & Thoughtful)."
        else:
            project.voice = "rachel"
            change_summary = "Switched narrator voice."
        success = True

    else:
        # Unsupported command! Do NOT mutate canonical state.
        success = False
        change_summary = (
            f"I couldn't recognize '{raw_cmd}'. Supported creator commands:\n"
            "- Make the hook stronger\n"
            "- Make this more provocative\n"
            "- Make this 20 seconds\n"
            "- Make this shorter\n"
            "- Make this more technical\n"
            "- Make it sound more conversational\n"
            "- Use simpler language\n"
            "- Replace scene N\n"
            "- Change the visual for scene N\n"
            "- Give me a stronger ending\n"
            "- Remove unnecessary repetition"
        )

    if success:
        if project.metrics:
            project.metrics.has_used_ask_vidsnap = True
        # Re-sync script & feedback
        combined = " ".join([s.narration or s.caption for s in project.scenes if (s.narration or s.caption)])
        if combined:
            project.script = combined
        if project.generated_story:
            project.qualitative_feedback = evaluate_story_qualitative(project.generated_story, project.scenes)
        db.save_project(project)

    return {
        "status": "success" if success else "unsupported",
        "success": success,
        "action": change_summary,
        "change_summary": change_summary,
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
