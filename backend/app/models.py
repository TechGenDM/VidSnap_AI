import uuid
from datetime import datetime, timezone
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

class VisualPlan(BaseModel):
    scene_id: int
    visual_type: str = "developer_workstation"
    subject: str = "creator"
    environment: str = "modern workspace"
    composition: str = "medium_close_up"
    mood: str = "focused"
    motion: str = "slow_zoom_in"
    transition: str = "crossfade"
    emphasis: str = "key insight"

class CaptionWord(BaseModel):
    text: str
    start_time: float
    end_time: float
    emphasized: bool = False

class CaptionSegment(BaseModel):
    text: str
    start_time: float = 0.0
    end_time: float = 0.0
    words: list[CaptionWord] = Field(default_factory=list)
    emphasis_words: list[str] = Field(default_factory=list)
    style: str = "kinetic" # "kinetic" | "emphasis" | "highlight"

class StoryScene(BaseModel):
    order: int
    narration: str = Field(..., min_length=3)
    caption: str = Field(..., min_length=1)
    visual_direction: str = Field(..., min_length=3)
    estimated_duration: float = Field(default=4.0, ge=0.5, le=60.0)
    scene_role: Optional[str] = "insight"
    visual_plan: Optional[VisualPlan] = None
    caption_segment: Optional[CaptionSegment] = None
    caption_segments: list[CaptionSegment] = Field(default_factory=list)
    visual_source: Optional[str] = "stock" # "ai" | "stock" | "fallback_stock"

class Story(BaseModel):
    title: str = Field(..., min_length=3)
    hook: str = Field(..., min_length=3)
    scenes: list[StoryScene] = Field(..., min_length=1)
    cta: str = Field(..., min_length=2)
    estimated_duration: float = Field(default=0.0, ge=0.0)
    hook_strategy: Optional[str] = None
    quality_score: Optional[float] = None
    domain: Optional[str] = None

class Scene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order: int
    visual_filename: str = "1.jpg"
    visual_url: str = "/media/templates/1.jpg"
    visual_direction: str = ""
    narration: str = ""
    caption: str = ""
    duration_seconds: float = 0.0
    scene_role: Optional[str] = "insight"
    match_quality: Optional[str] = "approximate"
    visual_plan: Optional[VisualPlan] = None
    caption_segment: Optional[CaptionSegment] = None
    caption_segments: list[CaptionSegment] = Field(default_factory=list)
    motion: Optional[str] = "slow_zoom_in"
    transition: Optional[str] = "crossfade"
    visual_source: Optional[str] = "stock" # "ai" | "stock" | "fallback_stock"
    alignment_source: Optional[str] = "estimated" # "native" | "transcription" | "estimated"

class LifecycleState(str, Enum):
    DRAFT = "draft"
    STORY_READY = "story_ready"
    RENDERING = "rendering"
    READY = "ready"
    FAILED = "failed"

class CreationMetrics(BaseModel):
    story_generation_ms: Optional[float] = None
    tts_generation_ms: Optional[float] = None
    render_ms: Optional[float] = None
    total_creation_ms: Optional[float] = None
    time_to_first_story_ms: Optional[float] = None
    time_to_first_preview_ms: Optional[float] = None
    time_to_final_reel_ms: Optional[float] = None

class ProjectVersion(BaseModel):
    version_number: int
    created_at: str
    label: str # e.g. "Initial Story", "Regenerated Story", "Ask VidSnap: Make shorter"
    title: str
    script: str
    hook: str
    duration_seconds: float
    voice: str
    music: Optional[str] = None
    style: str
    mode: str
    source_type: str = "quick"
    visual_source: str = "auto"
    audience: Optional[str] = None
    tone: Optional[str] = None
    target_length: Optional[str] = None
    scenes: list[Scene] = Field(default_factory=list)
    generated_story: Optional[Story] = None
    video_url: Optional[str] = None
    video_filename: Optional[str] = None
    thumbnail_url: Optional[str] = None
    lifecycle_state: LifecycleState = LifecycleState.STORY_READY
    quality_gate: Optional[dict] = None
    quality_warnings: list[str] = Field(default_factory=list)

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: JobStatus = JobStatus.QUEUED
    lifecycle_state: LifecycleState = LifecycleState.DRAFT
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
    visual_source: str = "auto" # "auto" | "ai" | "local"
    active_preset: Optional[str] = None
    original_prompt: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    target_length: Optional[str] = None
    generated_story: Optional[Story] = None
    render_history: list[dict] = Field(default_factory=list)
    generation_diagnostics: list[dict] = Field(default_factory=list)
    versions: list[ProjectVersion] = Field(default_factory=list)
    metrics: CreationMetrics = Field(default_factory=CreationMetrics)
    qualitative_feedback: list[str] = Field(default_factory=list)
    quality_gate: Optional[dict] = None
    quality_warnings: list[str] = Field(default_factory=list)

    def create_snapshot(self, label: str) -> ProjectVersion:
        """
        Creates an immutable, deep-copied snapshot of the complete canonical project state.
        Preserves all story, scene, audio, visual, and render-affecting configuration.
        """
        import copy
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        next_version_num = len(self.versions) + 1
        
        # Deep copy scenes and story
        copied_scenes = [Scene.model_validate(s.model_dump()) for s in self.scenes]
        copied_story = Story.model_validate(self.generated_story.model_dump()) if self.generated_story else None
        hook_text = copied_story.hook if copied_story else (copied_scenes[0].narration if copied_scenes else "")

        snapshot = ProjectVersion(
            version_number=next_version_num,
            created_at=now,
            label=label,
            title=self.title,
            script=self.script,
            hook=hook_text,
            duration_seconds=self.duration_seconds,
            voice=self.voice,
            music=self.music,
            style=self.style,
            mode=self.mode,
            source_type=self.source_type,
            visual_source=self.visual_source,
            audience=self.audience,
            tone=self.tone,
            target_length=self.target_length,
            scenes=copied_scenes,
            generated_story=copied_story,
            video_url=self.video_url,
            video_filename=self.video_filename,
            thumbnail_url=self.thumbnail_url,
            lifecycle_state=self.lifecycle_state,
            quality_gate=self.quality_gate,
            quality_warnings=list(self.quality_warnings),
        )
        self.versions.append(snapshot)
        return snapshot

    def restore_version(self, version_number: int) -> ProjectVersion:
        """
        Restores canonical state from a specific historical snapshot.
        Before restoring, automatically snapshots current state so no work is ever lost.
        Restoring produces a brand new current state from the snapshot.
        """
        target_version = next((v for v in self.versions if v.version_number == version_number), None)
        if not target_version:
            raise ValueError(f"Version {version_number} does not exist.")

        # Capture current state before restoring
        self.create_snapshot(f"Pre-restore snapshot (before reverting to v{version_number})")

        # Deep-copy attributes from snapshot into current project state
        self.title = target_version.title
        self.script = target_version.script
        self.duration_seconds = target_version.duration_seconds
        self.voice = target_version.voice
        self.music = target_version.music
        self.style = target_version.style
        self.mode = target_version.mode
        self.source_type = target_version.source_type
        self.visual_source = target_version.visual_source
        self.audience = target_version.audience
        self.tone = target_version.tone
        self.target_length = target_version.target_length
        self.lifecycle_state = target_version.lifecycle_state
        self.video_url = target_version.video_url
        self.video_filename = target_version.video_filename
        self.thumbnail_url = target_version.thumbnail_url
        self.quality_gate = target_version.quality_gate
        self.quality_warnings = list(target_version.quality_warnings)

        self.scenes = [Scene.model_validate(s.model_dump()) for s in target_version.scenes]
        self.generated_story = (
            Story.model_validate(target_version.generated_story.model_dump())
            if target_version.generated_story
            else None
        )

        # Record a fresh restore snapshot
        restore_snapshot = self.create_snapshot(f"Restored from Version {version_number}: '{target_version.label}'")
        return restore_snapshot

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    status: JobStatus = JobStatus.QUEUED
    step: str = "Understanding your idea"
    progress_percent: int = 5
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

