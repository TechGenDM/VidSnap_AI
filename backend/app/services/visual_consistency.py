"""
VidSnap AI - Visual Consistency Engine (Phase 7)
Provides best-effort visual continuity across consecutive scenes of a Reel.

Architecture:
- Establishes a shared ReelWorldContext (environment, palette, lighting, subject anchor)
- Guides varied camera shot progression (Hook: close-up, Context: wide, Insight: over-the-shoulder, Resolution: hero)
- Honest Framing: Treats visual continuity as best-effort stylistic and environmental alignment,
  avoiding false claims of guaranteed identity locking.
"""

from typing import Optional
from pydantic import BaseModel, Field
from app.models import StoryScene, VisualPlan


class ReelWorldContext(BaseModel):
    """
    Canonical environmental and stylistic world anchor shared across scenes of a Reel.
    """
    domain: str = "technology"
    visual_style: str = "cinematic"
    world_setting: str
    lighting_palette: str
    subject_anchor: str
    continuity_level: str = "best_effort_continuity"


class VisualConsistencyEngine:
    """
    Establishes world context and ensures cinematic shot progression
    while preventing random stylistic jumps across scenes.
    """

    WORLD_PRESETS = {
        "technology": {
            "world_setting": "sleek minimalist engineering studio with ambient edge lighting and architectural glass",
            "lighting_palette": "deep obsidian with vibrant cyan accents and soft warm rim light",
            "subject_anchor": "focused tech creator and developer orchestrating intelligent systems",
        },
        "education": {
            "world_setting": "clean modern conceptual lab with illuminated visual knowledge interfaces",
            "lighting_palette": "crisp balanced daylight with deep indigo and amber highlights",
            "subject_anchor": "thoughtful educator and researcher breaking down complex principles",
        },
        "business": {
            "world_setting": "contemporary executive innovation studio with panoramic city horizon glass",
            "lighting_palette": "warm architectural lighting with gold accents and high-contrast obsidian",
            "subject_anchor": "founder and strategist reviewing product growth and customer traction",
        },
        "science": {
            "world_setting": "atmospheric research laboratory with physical simulation equipment",
            "lighting_palette": "cinematic neutral lighting with spectral light dispersion and natural atmospheric glow",
            "subject_anchor": "analytical scientist observing natural phenomena and empirical models",
        },
        "personal": {
            "world_setting": "intimate creator studio with warm timber desk, natural window light, and notebooks",
            "lighting_palette": "soft directional daylight with cozy warm ambient tones",
            "subject_anchor": "authentic builder reflecting on personal lessons and real project milestones",
        },
    }

    # Standard 4-part cinematic shot progression
    SHOT_PROGRESSION = [
        {"composition": "tight_close_up", "motion": "slow_zoom_in", "role": "hook"},
        {"composition": "wide_environment", "motion": "pan_left", "role": "context"},
        {"composition": "over_the_shoulder_focus", "motion": "tilt_up", "role": "insight"},
        {"composition": "hero_medium_shot", "motion": "slow_zoom_out", "role": "resolution"},
    ]

    @classmethod
    def create_world_context(
        cls,
        domain: str = "technology",
        visual_style: str = "cinematic",
        topic: str = "",
    ) -> ReelWorldContext:
        """
        Creates a coherent ReelWorldContext for the project.
        """
        norm_domain = domain.lower() if domain.lower() in cls.WORLD_PRESETS else "technology"
        preset = cls.WORLD_PRESETS[norm_domain]

        return ReelWorldContext(
            domain=norm_domain,
            visual_style=visual_style,
            world_setting=preset["world_setting"],
            lighting_palette=preset["lighting_palette"],
            subject_anchor=preset["subject_anchor"],
            continuity_level="best_effort_continuity",
        )

    @classmethod
    def apply_world_continuity_to_scenes(
        cls,
        scenes: list[StoryScene],
        world: ReelWorldContext,
    ) -> list[StoryScene]:
        """
        Applies world context across scenes ensuring varied shots and avoiding consecutive duplicates.
        """
        last_visual_type = None

        for idx, scene in enumerate(scenes):
            progression_idx = min(idx, len(cls.SHOT_PROGRESSION) - 1)
            shot_guide = cls.SHOT_PROGRESSION[progression_idx]

            if not scene.visual_plan:
                scene.visual_plan = VisualPlan(
                    scene_id=scene.order,
                    visual_type="workstation_scene",
                    subject=world.subject_anchor,
                    environment=world.world_setting,
                    composition=shot_guide["composition"],
                    mood="focused and cinematic",
                    motion=shot_guide["motion"],
                    transition="crossfade" if idx > 0 else "cut",
                    emphasis="world continuity",
                    description=f"Scene {idx+1} in {world.world_setting}",
                )
            else:
                # Harmonize environment and lighting while preserving scene-specific subject focus
                if not scene.visual_plan.environment or scene.visual_plan.environment == "default":
                    scene.visual_plan.environment = world.world_setting
                # Maintain varied compositions
                if not scene.visual_plan.composition:
                    scene.visual_plan.composition = shot_guide["composition"]

            # Anti-consecutive duplicate visual type rule
            if scene.visual_plan.visual_type == last_visual_type:
                alt_types = ["architecture_flowchart", "developer_workstation", "metrics_dashboard", "global_network"]
                for alt in alt_types:
                    if alt != last_visual_type:
                        scene.visual_plan.visual_type = alt
                        break

            last_visual_type = scene.visual_plan.visual_type

        return scenes

    @classmethod
    def format_continuity_prompt(
        cls,
        base_prompt: str,
        world: ReelWorldContext,
        composition: str = "cinematic framing",
    ) -> str:
        """
        Enhances prompt with best-effort world consistency tokens.
        """
        continuity_tokens = (
            f"Set within {world.world_setting}, color palette of {world.lighting_palette}, "
            f"featuring {world.subject_anchor}, shot in {composition.replace('_', ' ')}, "
            f"consistent cinematic lighting, cohesive aesthetic continuity"
        )
        return f"{base_prompt}, {continuity_tokens}"
