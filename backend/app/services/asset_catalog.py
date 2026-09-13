"""
VidSnap AI - Asset Metadata Catalog (Phase 3)
Provides structured, maintainable metadata for local visual template assets.
Evaluates semantic overlap, visual types, subjects, moods, and composition
while strictly enforcing anti-consecutive-duplicate and nearby diversity rules.
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from app.models import VisualPlan

logger = logging.getLogger("vidsnap.services.asset_catalog")

@dataclass
class AssetMetadata:
    id: str
    filename: str
    tags: list[str]
    moods: list[str]
    composition: str
    subjects: list[str]
    visual_types: list[str]

# Curated catalog for local templates in media/templates/
CATALOG_ASSETS: list[AssetMetadata] = [
    AssetMetadata(
        id="template_1",
        filename="1.jpg",
        tags=["technology", "developer", "workspace", "computer", "dark", "code", "ide", "syntax", "editor", "terminal", "programming", "software"],
        moods=["focused", "analytical", "intense"],
        composition="medium_close_up",
        subjects=["developer", "laptop", "code_screen"],
        visual_types=["developer_workstation", "code_editor", "software_engineering"],
    ),
    AssetMetadata(
        id="template_2",
        filename="2.jpg",
        tags=["architecture", "flowchart", "network", "system", "infrastructure", "abstract", "connected", "nodes", "graph", "microservices", "cloud", "packets", "data"],
        moods=["visionary", "analytical", "technical"],
        composition="wide_context",
        subjects=["network_graph", "cloud_nodes", "system_topology"],
        visual_types=["global_network", "architecture_flowchart", "distributed_systems"],
    ),
    AssetMetadata(
        id="template_3",
        filename="3.jpg",
        tags=["creator", "lifestyle", "coffee", "desk", "clean", "workspace", "founder", "minimalist", "office", "laptop", "workstation", "personal", "reflection"],
        moods=["thoughtful", "reflective", "creative", "calm"],
        composition="overhead_desk",
        subjects=["creator", "founder_desk", "laptop"],
        visual_types=["lifestyle_workspace", "founder_desk", "creative_studio"],
    ),
    AssetMetadata(
        id="template_4",
        filename="4.jpg",
        tags=["dashboard", "metrics", "analytics", "growth", "graph", "screen", "charts", "launch", "velocity", "data", "business", "retention", "scale"],
        moods=["concrete", "urgent", "focused", "analytical"],
        composition="macro_focus",
        subjects=["analytics_chart", "product_metrics", "dashboard_ui"],
        visual_types=["metrics_dashboard", "performance_growth", "data_analytics"],
    ),
    AssetMetadata(
        id="template_5",
        filename="5.jpg",
        tags=["city", "horizon", "future", "modern", "night", "buildings", "global", "connected", "lights", "skyline", "atmosphere", "sky", "science", "world"],
        moods=["visionary", "inviting", "inspirational", "atmospheric"],
        composition="wide_landscape",
        subjects=["city_skyline", "modern_horizon", "atmospheric_sky"],
        visual_types=["atmospheric_sky", "city_horizon", "global_future"],
    ),
]

class AssetCatalog:
    """
    Asset Catalog service responsible for scoring and selecting local assets
    based on the scene's VisualPlan and contextual criteria.
    """

    def __init__(self, assets: Optional[list[AssetMetadata]] = None):
        self.assets = assets or CATALOG_ASSETS

    def get_asset_by_filename(self, filename: str) -> Optional[AssetMetadata]:
        for a in self.assets:
            if a.filename == filename:
                return a
        return None

    def get_all_assets(self) -> list[AssetMetadata]:
        return list(self.assets)

    def score_asset(
        self,
        asset: AssetMetadata,
        visual_plan: Optional[VisualPlan],
        scene_text: str,
        domain: str = "technology",
        visual_style: str = "Minimal Tech",
    ) -> float:
        """
        Calculates a deterministic semantic match score between an asset and the scene's visual plan.
        Weights:
        - Visual Type Match: 4.0
        - Subject Match: 2.5
        - Tag Overlap: 1.0 per match
        - Mood Match: 1.5
        - Composition Match: 1.0
        """
        score = 0.0
        text_lower = scene_text.lower()

        # Tag overlap
        tag_matches = sum(1 for t in asset.tags if t in text_lower)
        score += min(5.0, tag_matches * 1.0)

        if visual_plan:
            # Visual type
            if visual_plan.visual_type in asset.visual_types or any(vt in visual_plan.visual_type for vt in asset.visual_types):
                score += 4.0

            # Subject match
            if visual_plan.subject in asset.subjects or any(s in visual_plan.subject for s in asset.subjects):
                score += 2.5

            # Mood match
            if visual_plan.mood in asset.moods or any(m in visual_plan.mood for m in asset.moods):
                score += 1.5

            # Composition match
            if visual_plan.composition == asset.composition:
                score += 1.0

        # Domain contextual alignment
        if domain == "technology" and any(t in asset.tags for t in ["technology", "code", "network", "ide"]):
            score += 1.0
        elif domain == "business" and any(t in asset.tags for t in ["dashboard", "metrics", "growth", "founder"]):
            score += 1.0
        elif domain == "science" and any(t in asset.tags for t in ["atmosphere", "sky", "network"]):
            score += 1.0
        elif domain == "personal" and any(t in asset.tags for t in ["creator", "desk", "lifestyle", "laptop"]):
            score += 1.0

        return round(score, 2)

    def select_best_asset(
        self,
        visual_plan: Optional[VisualPlan],
        scene_text: str,
        domain: str,
        visual_style: str,
        previously_used: list[str],
    ) -> tuple[AssetMetadata, str]:
        """
        Selects the best asset respecting:
        1. Anti-consecutive-duplicate rule: asset must differ from previously_used[-1] if alternatives exist.
        2. Nearby scene penalty: assets used in the last 2 scenes receive a penalty.
        3. Returns (AssetMetadata, match_quality: "exact" | "approximate").
        """
        scored_candidates: list[tuple[float, AssetMetadata]] = []
        last_used = previously_used[-1] if previously_used else None
        recent_used = previously_used[-2:] if len(previously_used) >= 2 else previously_used

        for asset in self.assets:
            base_score = self.score_asset(
                asset=asset,
                visual_plan=visual_plan,
                scene_text=scene_text,
                domain=domain,
                visual_style=visual_style,
            )

            # Apply strict disqualification or heavy penalty for consecutive repeat
            if last_used and asset.filename == last_used and len(self.assets) > 1:
                base_score -= 100.0 # Force different asset if available

            # Penalize recent reuse
            if asset.filename in recent_used and len(self.assets) > 2:
                base_score -= 2.0

            scored_candidates.append((base_score, asset))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_asset = scored_candidates[0]

        # Determine honest match quality
        # An exact match requires a positive base score >= 3.5 without penalties
        raw_score = self.score_asset(
            asset=best_asset,
            visual_plan=visual_plan,
            scene_text=scene_text,
            domain=domain,
            visual_style=visual_style,
        )
        match_quality = "exact" if raw_score >= 3.5 else "approximate"

        return best_asset, match_quality

default_asset_catalog = AssetCatalog()
