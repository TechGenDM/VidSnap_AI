from typing import Optional
from pydantic import BaseModel, Field
from app.models import JobStatus, Scene, Story, StoryScene, VisualPlan, CaptionSegment

class QuickReelCreate(BaseModel):
    script: str = Field(..., min_length=3, max_length=5000)
    voice: str = "adam"
    music: Optional[str] = "ambient_chill"
    style: str = "cinematic"
    image_order: Optional[list[str]] = None # List of filenames in desired order

class AIReelCreate(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=1000)
    audience: str = "Tech Creators"
    tone: str = "Educational"
    length: str = "30s"
    visual_style: str = "Minimal Tech"
    voice: str = "adam"
    music: Optional[str] = "ambient_chill"
    visual_source: str = "auto" # "auto" | "ai" | "local"
    preset: Optional[str] = None

class ApplyHookRequest(BaseModel):
    hook: str
    caption: Optional[str] = None

class SceneUpdate(BaseModel):
    id: str
    narration: Optional[str] = None
    caption: Optional[str] = None
    visual_direction: Optional[str] = None
    visual_filename: Optional[str] = None
    visual_url: Optional[str] = None
    scene_role: Optional[str] = None
    motion: Optional[str] = None
    transition: Optional[str] = None
    duration_seconds: Optional[float] = None
    visual_prompt: Optional[str] = None
    visual_plan: Optional[VisualPlan] = None
    visual_source: Optional[str] = None

class UpdateProjectScenes(BaseModel):
    scenes: list[SceneUpdate]

class RegenerateSceneRequest(BaseModel):
    feedback: Optional[str] = None

class RegenerateVisualRequest(BaseModel):
    prompt: Optional[str] = None
    seed: Optional[int] = None

class SelectVisualRequest(BaseModel):
    visual_filename: str
    visual_url: str
    visual_type: Optional[str] = "custom_selected"

class QualityGateResponse(BaseModel):
    passed: bool
    is_ready_to_post: bool
    warnings: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)

class AssistantRequest(BaseModel):
    command: str

class StoryPlanResponse(BaseModel):
    project_id: str
    status: str
    story: Story
    scenes: list[Scene]
    message: str

class JobResponse(BaseModel):
    id: str
    project_id: str
    status: JobStatus
    step: str
    progress_percent: int
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    title: str
    created_at: str
    status: JobStatus
    lifecycle_state: str = "draft"
    duration_seconds: float
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    voice: str
    music: Optional[str] = None
    style: str
    script: str
    scenes: list[Scene]
    mode: str
    source_type: str = "quick"
    visual_source: str = "auto"
    active_preset: Optional[str] = None
    original_prompt: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    target_length: Optional[str] = None
    generated_story: Optional[Story] = None
    render_history: list[dict] = Field(default_factory=list)
    generation_diagnostics: list[dict] = Field(default_factory=list)
    versions: list[dict] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    qualitative_feedback: list[str] = Field(default_factory=list)
    quality_gate: Optional[dict] = None
    quality_warnings: list[str] = Field(default_factory=list)

class MusicTrackResponse(BaseModel):
    id: str
    title: str
    genre: str
    filename: str

class VoiceResponse(BaseModel):
    id: str
    name: str
    accent: str
    gender: str
    description: str
