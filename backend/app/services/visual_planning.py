"""
VidSnap AI - Visual Planning Engine (Phase 3)
Produces structured VisualPlan objects for StoryScenes before asset retrieval.
Decouples scene reasoning (composition, mood, camera motion, transitions)
from asset retrieval and video rendering.
"""

import logging
from typing import Optional
from app.models import StoryScene, VisualPlan

logger = logging.getLogger("vidsnap.services.visual_planning")

class VisualPlanningEngine:
    """
    Evaluates each scene's narrative purpose, scene role, narration, caption,
    domain, and tone to build a coherent, cinematic VisualPlan.
    """

    @classmethod
    def plan_scene_visuals(
        cls,
        scene: StoryScene,
        domain: str = "technology",
        tone: str = "Educational",
        visual_style: str = "Minimal Tech",
    ) -> VisualPlan:
        role = (scene.scene_role or "insight").lower()
        narration_lower = scene.narration.lower()
        style_lower = visual_style.lower()

        # 1. Determine Subject & Visual Type based on Domain + Narration keywords
        if domain == "technology":
            if any(k in narration_lower for k in ["syntax", "code", "developer", "typing", "function", "line"]):
                visual_type = "developer_workstation"
                subject = "developer"
                environment = f"dark minimalist workspace in {style_lower}"
            elif any(k in narration_lower for k in ["agent", "orchestrat", "network", "system", "architecture", "microservice"]):
                visual_type = "architecture_flowchart"
                subject = "cloud_nodes"
                environment = "abstract illuminated architecture space"
            elif any(k in narration_lower for k in ["speed", "velocity", "hour", "month", "leverage"]):
                visual_type = "metrics_dashboard"
                subject = "product_metrics"
                environment = "sleek analytics studio"
            else:
                visual_type = "global_network"
                subject = "network_graph"
                environment = f"modern tech studio in {style_lower}"

        elif domain == "science":
            if any(k in narration_lower for k in ["sky", "atmosphere", "blue", "sunset", "red", "orange"]):
                visual_type = "atmospheric_sky"
                subject = "atmospheric_sky"
                environment = "wide open atmospheric sky during natural sunlight"
            elif any(k in narration_lower for k in ["molecule", "particle", "scatter", "wave", "light", "rayleigh"]):
                visual_type = "global_network"
                subject = "cloud_nodes"
                environment = "abstract simulation of particle scattering"
            else:
                visual_type = "city_horizon"
                subject = "city_skyline"
                environment = "horizon with natural atmospheric lighting"

        elif domain == "education":
            if any(k in narration_lower for k in ["packet", "route", "router", "fiber", "cable", "ocean"]):
                visual_type = "global_network"
                subject = "network_graph"
                environment = "illuminated global data transmission pathways"
            elif any(k in narration_lower for k in ["device", "phone", "server", "protocol"]):
                visual_type = "developer_workstation"
                subject = "laptop"
                environment = "clean connected digital device workspace"
            else:
                visual_type = "architecture_flowchart"
                subject = "system_topology"
                environment = "educational concept diagram"

        elif domain == "business":
            if any(k in narration_lower for k in ["customer", "market", "pull", "demand", "founder", "talk"]):
                visual_type = "founder_desk"
                subject = "founder"
                environment = "minimalist creator studio desk"
            elif any(k in narration_lower for k in ["feature", "metrics", "product", "growth", "revenue", "fit"]):
                visual_type = "metrics_dashboard"
                subject = "product_metrics"
                environment = "high-contrast metrics and user retention screen"
            else:
                visual_type = "creative_studio"
                subject = "creator"
                environment = "modern executive strategy workspace"

        else: # personal
            if any(k in narration_lower for k in ["prototype", "model", "build", "project", "code"]):
                visual_type = "developer_workstation"
                subject = "developer"
                environment = "focused late-night maker workstation"
            elif any(k in narration_lower for k in ["user", "feedback", "lesson", "public"]):
                visual_type = "lifestyle_workspace"
                subject = "creator"
                environment = "clean minimalist daylight workspace with coffee"
            else:
                visual_type = "city_horizon"
                subject = "modern_horizon"
                environment = "atmospheric wide view symbolizing future growth"

        # 2. Composition, Mood, Motion, and Transition based on Scene Role & Tone
        if role == "hook":
            composition = "medium_close_up"
            mood = "urgent" if "energy" in tone.lower() else "focused"
            motion = "slow_zoom_in" # Faster, punchy focus on the core opening tension
            transition = "short_fade" if "thoughtful" in tone.lower() else "cut"
            emphasis = "opening tension"
        elif role == "context":
            composition = "wide_context"
            mood = "analytical" if "education" in tone.lower() else "reflective"
            motion = "pan_left"
            transition = "crossfade"
            emphasis = "broad framing"
        elif role == "insight":
            composition = "macro_focus"
            mood = "focused"
            motion = "slow_zoom_in" # Controlled, deliberate movement drawing focus to the key takeaway
            transition = "crossfade"
            emphasis = "core revelation"
        elif role == "example":
            composition = "overhead_desk"
            mood = "concrete"
            motion = "pan_right"
            transition = "directional_slide"
            emphasis = "practical illustration"
        else: # implication or cta
            composition = "clean_center"
            mood = "visionary" if "energy" in tone.lower() else "inviting"
            motion = "static_hold" if role == "cta" else "slow_zoom_out"
            transition = "crossfade"
            emphasis = "final payoff"

        plan = VisualPlan(
            scene_id=scene.order,
            visual_type=visual_type,
            subject=subject,
            environment=environment,
            composition=composition,
            mood=mood,
            motion=motion,
            transition=transition,
            emphasis=emphasis,
        )
        return plan

    @classmethod
    def plan_story_visuals(
        cls,
        scenes: list[StoryScene],
        domain: str = "technology",
        tone: str = "Educational",
        visual_style: str = "Minimal Tech",
    ) -> list[VisualPlan]:
        """Plans visuals across all scenes in a story."""
        plans = []
        for s in scenes:
            plan = cls.plan_scene_visuals(
                scene=s,
                domain=domain,
                tone=tone,
                visual_style=visual_style,
            )
            plans.append(plan)
        return plans
