"""
VidSnap AI - Render Plan Architecture (Phase 3)
Defines the RenderPlan, SceneRenderItem, AudioRenderPlan, and RenderPlanBuilder.
The RenderPlan is the single source of truth for the FFmpeg video rendering engine.
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from app.models import Project, VisualPlan, CaptionSegment
from app.services.motion import MotionEngine
from app.services.storage import get_project_dir

logger = logging.getLogger("vidsnap.services.render_plan")

SUPPORTED_TRANSITIONS = {"cut", "short_fade", "crossfade", "directional_slide"}


@dataclass
class SceneRenderItem:
    scene_id: str
    order: int
    image_path: Path
    duration: float
    caption: str
    motion: str
    transition: str
    visual_plan: Optional[VisualPlan] = None
    caption_segment: Optional[CaptionSegment] = None
    caption_segments: list[CaptionSegment] = field(default_factory=list)


@dataclass
class AudioRenderPlan:
    audio_path: Path
    total_duration: float
    music_path: Optional[Path] = None
    music_volume: float = 0.12
    ducking_enabled: bool = True


@dataclass
class RenderPlan:
    project_id: str
    scenes: list[SceneRenderItem]
    audio: AudioRenderPlan
    output_path: Path
    width: int = 1080
    height: int = 1920
    fps: int = 30

    def validate(self) -> list[str]:
        """
        Validates the complete render plan before any FFmpeg invocation.
        Returns a list of validation error strings. If empty, the plan is valid.
        """
        errors: list[str] = []

        if not self.scenes:
            errors.append("RenderPlan must contain at least one scene.")

        for idx, s in enumerate(self.scenes):
            if not s.image_path.exists():
                errors.append(f"Scene {s.order} image file does not exist: {s.image_path}")
            if s.duration <= 0.05:
                errors.append(f"Scene {s.order} duration ({s.duration}s) must be greater than 0.05s.")
            if s.motion not in MotionEngine.SUPPORTED_MOTIONS:
                errors.append(f"Scene {s.order} motion '{s.motion}' is not supported.")
            if s.transition not in SUPPORTED_TRANSITIONS:
                errors.append(f"Scene {s.order} transition '{s.transition}' is not supported.")

        if not self.audio.audio_path.exists():
            errors.append(f"Audio file does not exist: {self.audio.audio_path}")

        if self.audio.total_duration <= 0.2:
            errors.append(f"Audio duration ({self.audio.total_duration}s) is too short.")

        if self.audio.music_path and not self.audio.music_path.exists():
            errors.append(f"Music track file does not exist: {self.audio.music_path}")

        if self.width <= 0 or self.height <= 0:
            errors.append(f"Invalid canvas dimensions: {self.width}x{self.height}")

        if self.fps not in {24, 25, 30, 60}:
            errors.append(f"Unsupported frame rate: {self.fps}")

        return errors


class RenderPlanBuilder:
    """
    Constructs a validated RenderPlan from a Project and Audio metadata.
    """

    @classmethod
    def build_from_project(
        cls,
        project: Project,
        audio_path: Path,
        total_audio_duration: float,
        output_video_path: Path,
        music_path: Optional[Path] = None,
        fps: int = 30,
    ) -> RenderPlan:
        num_scenes = len(project.scenes)
        if num_scenes == 0:
            raise ValueError("Cannot build RenderPlan: Project has no scenes.")

        project_dir = get_project_dir(project.id)

        # Distribute audio duration across scenes
        # If scenes have estimated durations, weight accordingly; otherwise equal split
        est_durations = [s.duration_seconds for s in project.scenes if s.duration_seconds and s.duration_seconds > 0]
        if len(est_durations) == num_scenes and sum(est_durations) > 0:
            total_est = sum(est_durations)
            durations = [(d / total_est) * total_audio_duration for d in est_durations]
        else:
            uniform_dur = total_audio_duration / num_scenes
            durations = [uniform_dur] * num_scenes

        scene_items: list[SceneRenderItem] = []
        for idx, scene in enumerate(project.scenes):
            # Resolve image path
            img_path = None
            if scene.visual_filename:
                candidate = project_dir / scene.visual_filename
                if candidate.exists():
                    img_path = candidate

            if not img_path:
                # Check media/templates or fallback
                from app.config import settings
                fallback_template = settings.TEMPLATES_DIR / f"{(idx % 5) + 1}.jpg"
                if fallback_template.exists():
                    img_path = fallback_template
                else:
                    raise FileNotFoundError(f"Visual asset for scene {scene.order} could not be resolved.")

            # Motion & Transition defaults if not set
            motion = MotionEngine.normalize_motion(scene.motion or (scene.visual_plan.motion if scene.visual_plan else None))
            raw_trans = scene.transition or (scene.visual_plan.transition if scene.visual_plan else None) or "crossfade"
            transition = raw_trans if raw_trans in SUPPORTED_TRANSITIONS else "crossfade"

            # In short reels or specific roles: hook -> cut/short_fade, insight -> crossfade, example -> directional_slide
            if not scene.transition:
                role = (scene.scene_role or "").lower()
                if role == "hook":
                    transition = "cut"
                elif role == "example":
                    transition = "directional_slide"
                else:
                    transition = "crossfade"

            # Build caption segments
            cap_segments = scene.caption_segments or []
            if not cap_segments and scene.caption_segment:
                cap_segments = [scene.caption_segment]
            elif not cap_segments and scene.caption:
                cap_words = [w.strip() for w in scene.caption.split() if w.strip()]
                cap_seg = CaptionSegment(
                    text=scene.caption,
                    start_time=0.0,
                    end_time=durations[idx],
                    emphasis_words=[cap_words[0]] if cap_words else [],
                    style="kinetic",
                )
                cap_segments = [cap_seg]

            cap_seg = cap_segments[0] if cap_segments else None

            item = SceneRenderItem(
                scene_id=scene.id,
                order=scene.order,
                image_path=img_path,
                duration=round(durations[idx], 3),
                caption=scene.caption or "",
                motion=motion,
                transition=transition,
                visual_plan=scene.visual_plan,
                caption_segment=cap_seg,
                caption_segments=cap_segments,
            )
            scene_items.append(item)

        audio_plan = AudioRenderPlan(
            audio_path=audio_path,
            total_duration=total_audio_duration,
            music_path=music_path,
            music_volume=0.12,
            ducking_enabled=True,
        )

        plan = RenderPlan(
            project_id=project.id,
            scenes=scene_items,
            audio=audio_plan,
            output_path=output_video_path,
            width=1080,
            height=1920,
            fps=fps,
        )

        errors = plan.validate()
        if errors:
            err_msg = f"Invalid RenderPlan for project {project.id}: {'; '.join(errors)}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        return plan
