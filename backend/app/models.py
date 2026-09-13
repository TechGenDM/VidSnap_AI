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

class Scene(BaseModel):
    id: str
    order: int
    visual_filename: str
    visual_url: str
    narration: str = ""
    caption: str = ""
    duration_seconds: float = 0.0

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
