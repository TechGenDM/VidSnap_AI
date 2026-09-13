from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    GENERATING_VOICE = "generating_voice"
    GENERATING_CAPTIONS = "generating_captions"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"

class StoryScene(BaseModel):
    order: int
    narration: str = Field(..., min_length=3)
    caption: str = Field(..., min_length=1)
    visual_direction: str = Field(..., min_length=3)
    estimated_duration: float = Field(default=4.0, ge=0.5, le=60.0)
    scene_role: Optional[str] = "insight"

class Story(BaseModel):
    title: str = Field(..., min_length=3)
    hook: str = Field(..., min_length=3)
    scenes: list[StoryScene] = Field(..., min_length=1)
    cta: str = Field(..., min_length=2)
    estimated_duration: float = Field(default=0.0, ge=0.0)
    hook_strategy: Optional[str] = None
    quality_score: Optional[float] = None

class Scene(BaseModel):
    id: str
    order: int
    visual_filename: str
    visual_url: str
    visual_direction: str = ""
    narration: str = ""
    caption: str = ""
    duration_seconds: float = 0.0
    scene_role: Optional[str] = "insight"
    match_quality: Optional[str] = "approximate"

class Project(BaseModel):
    id: str
    title: str
    created_at: str
    status: JobStatus = JobStatus.QUEUED
    duration_seconds: float = 0.0
    video_filename: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    voice: str = "adam"
    music: Optional[str] = "ambient_chill"
    style: str = "cinematic"
    script: str = ""
    scenes: list[Scene] = Field(default_factory=list)
    mode: str = "quick" # "quick" | "ai"
    source_type: str = "quick" # "quick" | "ai" | "future_repurpose"
    original_prompt: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    target_length: Optional[str] = None
    generated_story: Optional[Story] = None
    render_history: list[dict] = Field(default_factory=list)

class Job(BaseModel):
    id: str
    project_id: str
    status: JobStatus = JobStatus.QUEUED
    step: str = "Understanding your idea"
    progress_percent: int = 5
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
