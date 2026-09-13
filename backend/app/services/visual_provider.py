import shutil
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models import Scene, StoryScene, VisualPlan, CaptionSegment
from app.services.storage import get_project_dir
from app.services.asset_catalog import default_asset_catalog, AssetCatalog
from app.services.visual_planning import VisualPlanningEngine

logger = logging.getLogger("vidsnap.services.visual_provider")


class VisualProvider(ABC):
    """
    Abstract interface for matching or generating visual assets for story scenes.
    """

    @abstractmethod
    def match_visuals_for_scenes(
        self,
        scenes: list[StoryScene],
        visual_style: str,
        project_id: str,
        domain: str = "technology",
        tone: str = "Educational",
    ) -> list[Scene]:
        """Maps story scenes to concrete visual assets and visual plans for rendering."""
        pass


class LocalAssetProvider(VisualProvider):
    """
    Local Asset Provider matching story scenes with available local stock/template photography.
    Leverages AssetCatalog for structured semantic scoring, visual type alignment, mood/composition matching,
    and strict anti-consecutive-duplicate and nearby diversity enforcement.
    Assigns VisualPlan, Motion presets, and Scene-specific Transitions.
    Exposes whether a match is exact or approximate without claiming false AI comprehension.
    """

    def __init__(self, templates_dir: Optional[Path] = None, catalog: Optional[AssetCatalog] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self.catalog = catalog or default_asset_catalog

    def _get_available_templates(self) -> list[Path]:
        if not self.templates_dir.exists():
            return []
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        files = sorted([f for f in self.templates_dir.iterdir() if f.suffix.lower() in valid_exts])
        return files

    def match_visuals_for_scenes(
        self,
        scenes: list[StoryScene],
        visual_style: str,
        project_id: str,
        domain: str = "technology",
        tone: str = "Educational",
    ) -> list[Scene]:
        project_dir = get_project_dir(project_id)
        templates = self._get_available_templates()

        if not templates:
            logger.warning(f"No templates found in {self.templates_dir}. Creating emergency visual fallback.")
            from PIL import Image
            fallback_img = project_dir / "fallback.jpg"
            img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
            img.save(fallback_img, "JPEG")
            templates = [fallback_img]

        result_scenes: list[Scene] = []
        previously_used: list[str] = []

        for story_scene in scenes:
            # 1. Generate or retrieve structured VisualPlan
            visual_plan = story_scene.visual_plan
            if not visual_plan:
                visual_plan = VisualPlanningEngine.plan_scene_visuals(
                    scene=story_scene,
                    domain=domain,
                    tone=tone,
                    visual_style=visual_style,
                )
                story_scene.visual_plan = visual_plan

            # 2. Select best asset from catalog using visual plan and contextual rules
            scene_context = f"{story_scene.visual_direction} {story_scene.narration} {visual_style}"
            best_asset, match_quality = self.catalog.select_best_asset(
                visual_plan=visual_plan,
                scene_text=scene_context,
                domain=domain,
                visual_style=visual_style,
                previously_used=previously_used,
            )

            # Record used filename for diversity enforcement
            previously_used.append(best_asset.filename)

            # Locate source file in templates_dir
            src_template = self.templates_dir / best_asset.filename
            if not src_template.exists():
                # Fallback to whatever template is available
                src_template = templates[0] if templates else None

            dest_filename = f"scene_{story_scene.order}.jpg"
            dest_path = project_dir / dest_filename

            if src_template and src_template.exists():
                try:
                    shutil.copy2(src_template, dest_path)
                except Exception as e:
                    logger.error(f"Failed copying template {src_template} to {dest_path}: {e}")

            # 3. Create caption segment structure (future-ready for word-level karaoke timing)
            caption_words = [w.strip() for w in story_scene.caption.split() if w.strip()]
            emphasis = [caption_words[0]] if caption_words else []
            caption_segment = CaptionSegment(
                text=story_scene.caption,
                start_time=0.0,
                end_time=story_scene.estimated_duration,
                emphasis_words=emphasis,
                style="bold_pill",
            )

            # 4. Construct rich Scene object
            scene = Scene(
                id=f"scene_{story_scene.order}",
                order=story_scene.order,
                visual_filename=dest_filename,
                visual_url=f"/media/uploads/{project_id}/{dest_filename}",
                visual_direction=story_scene.visual_direction,
                narration=story_scene.narration,
                caption=story_scene.caption,
                duration_seconds=story_scene.estimated_duration,
                scene_role=story_scene.scene_role,
                match_quality=match_quality,
                visual_plan=visual_plan,
                caption_segment=caption_segment,
                motion=visual_plan.motion,
                transition=visual_plan.transition,
            )
            result_scenes.append(scene)

        return result_scenes


class FutureImageGenerationProvider(VisualProvider):
    """
    Reserved abstraction for future phases (DALL-E, Flux, Midjourney, Imagen, etc.).
    Keeps architectural boundary clean without prematurely integrating external generation APIs in Phase 3.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def match_visuals_for_scenes(
        self,
        scenes: list[StoryScene],
        visual_style: str,
        project_id: str,
        domain: str = "technology",
        tone: str = "Educational",
    ) -> list[Scene]:
        raise NotImplementedError(
            "FutureImageGenerationProvider is planned for a future phase. "
            "Phase 3 uses deterministic LocalAssetProvider with AssetCatalog."
        )


local_visual_provider = LocalAssetProvider()

