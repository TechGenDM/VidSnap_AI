"""
VidSnap AI - Visual Provider Architecture (Phase 4)
Orchestrates visual asset matching, real AI image generation, asset caching,
and rock-solid fallback to the local asset catalog.

Visual Source Modes:
- 'local': Uses deterministic local photography via AssetCatalog
- 'ai': Generates AI visuals for every scene with graceful fallback on provider error
- 'auto': Prefers high-confidence local assets and generates AI visuals when local match is insufficient
"""

import shutil
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models import Scene, StoryScene, VisualPlan, CaptionSegment
from app.services.storage import get_project_dir
from app.services.asset_catalog import default_asset_catalog, AssetCatalog
from app.services.visual_planning import VisualPlanningEngine
from app.services.image_generation import (
    ImageGenerationProvider,
    PollinationsImageProvider,
    VisualPromptBuilder,
    AssetCache,
    ImageGenerationError,
    default_image_provider,
    default_asset_cache,
)

logger = logging.getLogger("vidsnap.services.visual_provider")


class VisualProvider(ABC):
    """
    Abstract interface for matching or generating visual assets for story scenes.
    """
    def __init__(self):
        self.last_diagnostics: list[dict] = []

    @abstractmethod
    def match_visuals_for_scenes(
        self,
        scenes: list[StoryScene],
        visual_style: str,
        project_id: str,
        domain: str = "technology",
        tone: str = "Educational",
        visual_source_mode: str = "auto",
    ) -> list[Scene]:
        """
        Maps story scenes to concrete visual assets and visual plans for rendering.
        Returns scenes list. Diagnostics are saved to self.last_diagnostics.
        """
        pass


class LocalAssetProvider(VisualProvider):
    """
    Local Asset Provider matching story scenes with available local stock/template photography.
    Leverages AssetCatalog for structured semantic scoring, visual type alignment, mood/composition matching,
    and anti-consecutive-duplicate enforcement.
    """

    def __init__(self, templates_dir: Optional[Path] = None, catalog: Optional[AssetCatalog] = None):
        super().__init__()
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self.catalog = catalog or default_asset_catalog
        self.last_diagnostics: list[dict] = []

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
        visual_source_mode: str = "local",
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
        diagnostics: list[dict] = []
        previously_used: list[str] = []

        for story_scene in scenes:
            # 1. Structured VisualPlan
            visual_plan = story_scene.visual_plan
            if not visual_plan:
                visual_plan = VisualPlanningEngine.plan_scene_visuals(
                    scene=story_scene,
                    domain=domain,
                    tone=tone,
                    visual_style=visual_style,
                )
                story_scene.visual_plan = visual_plan

            # 2. Select asset from catalog
            scene_context = f"{story_scene.visual_direction} {story_scene.narration} {visual_style}"
            best_asset, match_quality = self.catalog.select_best_asset(
                visual_plan=visual_plan,
                scene_text=scene_context,
                domain=domain,
                visual_style=visual_style,
                previously_used=previously_used,
            )
            previously_used.append(best_asset.filename)

            src_template = self.templates_dir / best_asset.filename
            if not src_template.exists():
                src_template = templates[0] if templates else None

            dest_filename = f"scene_{story_scene.order}.jpg"
            dest_path = project_dir / dest_filename

            if src_template and src_template.exists():
                try:
                    shutil.copy2(src_template, dest_path)
                except Exception as e:
                    logger.error(f"Failed copying template {src_template} to {dest_path}: {e}")

            # 3. Initial caption segment
            caption_words = [w.strip() for w in story_scene.caption.split() if w.strip()]
            emphasis = [caption_words[0]] if caption_words else []
            caption_segment = CaptionSegment(
                text=story_scene.caption,
                start_time=0.0,
                end_time=story_scene.estimated_duration,
                emphasis_words=emphasis,
                style="bold_pill",
            )

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
                caption_segments=story_scene.caption_segments or [caption_segment],
                motion=visual_plan.motion,
                transition=visual_plan.transition,
                visual_source="stock",
                alignment_source="estimated",
            )
            result_scenes.append(scene)
            diagnostics.append({
                "scene_order": story_scene.order,
                "visual_source": "stock",
                "asset": best_asset.filename,
                "match_quality": match_quality,
            })

        self.last_diagnostics = diagnostics
        return result_scenes


class SmartVisualProvider(VisualProvider):
    """
    Intelligent Visual Provider combining real AI image generation, asset caching,
    and automatic LocalAssetProvider fallback.
    """

    def __init__(
        self,
        image_provider: Optional[ImageGenerationProvider] = None,
        asset_cache: Optional[AssetCache] = None,
        local_provider: Optional[LocalAssetProvider] = None,
    ):
        super().__init__()
        self.image_provider = image_provider or default_image_provider
        self.asset_cache = asset_cache or default_asset_cache
        self.local_provider = local_provider or LocalAssetProvider()
        self.last_diagnostics: list[dict] = []

    def match_visuals_for_scenes(
        self,
        scenes: list[StoryScene],
        visual_style: str,
        project_id: str,
        domain: str = "technology",
        tone: str = "Educational",
        visual_source_mode: str = "auto",
    ) -> list[Scene]:
        mode = (visual_source_mode or "auto").strip().lower()

        # If explicit local mode requested, delegate directly to LocalAssetProvider
        if mode == "local":
            logger.info(f"Visual source is 'local'. Using LocalAssetProvider for project {project_id}.")
            res = self.local_provider.match_visuals_for_scenes(
                scenes=scenes,
                visual_style=visual_style,
                project_id=project_id,
                domain=domain,
                tone=tone,
            )
            self.last_diagnostics = self.local_provider.last_diagnostics
            return res

        project_dir = get_project_dir(project_id)
        result_scenes: list[Scene] = []
        diagnostics: list[dict] = []
        previously_used: list[str] = []

        for story_scene in scenes:
            # 1. Ensure structured visual plan exists
            visual_plan = story_scene.visual_plan
            if not visual_plan:
                visual_plan = VisualPlanningEngine.plan_scene_visuals(
                    scene=story_scene,
                    domain=domain,
                    tone=tone,
                    visual_style=visual_style,
                )
                story_scene.visual_plan = visual_plan

            dest_filename = f"scene_{story_scene.order}.jpg"
            dest_path = project_dir / dest_filename
            scene_source = "stock"
            match_quality = "approximate"
            diag_entry: dict = {"scene_order": story_scene.order}

            # 2. Determine whether to generate AI or use local asset
            should_generate_ai = True
            if mode == "auto":
                # Check if catalog has high-confidence match
                scene_context = f"{story_scene.visual_direction} {story_scene.narration} {visual_style}"
                candidate_asset, quality = self.local_provider.catalog.select_best_asset(
                    visual_plan=visual_plan,
                    scene_text=scene_context,
                    domain=domain,
                    visual_style=visual_style,
                    previously_used=previously_used,
                )
                if quality == "exact":
                    logger.info(f"Auto visual selection: High-confidence stock match ({candidate_asset.filename}) found for scene {story_scene.order}.")
                    should_generate_ai = False

            # 3. Execution: AI Generation with Fallback
            if should_generate_ai:
                prompt = VisualPromptBuilder.build_prompt(
                    visual_plan=visual_plan,
                    visual_style=visual_style,
                    narration=story_scene.narration,
                    scene_role=story_scene.scene_role or "insight",
                )
                diag_entry["prompt"] = prompt

                # Compute deterministic asset cache key
                prompt_hash = self.asset_cache.compute_hash(
                    prompt=prompt,
                    model=getattr(self.image_provider, "model", "flux"),
                    width=576,
                    height=1024,
                    visual_style=visual_style,
                )
                diag_entry["prompt_hash"] = prompt_hash

                # Check cache first
                cached_file = self.asset_cache.get_cached_image(prompt_hash)
                if cached_file:
                    logger.info(f"AI asset cache HIT for scene {story_scene.order} ({prompt_hash}). Copying from cache.")
                    shutil.copy2(cached_file, dest_path)
                    scene_source = "ai"
                    match_quality = "ai_cached"
                    diag_entry["cache_hit"] = True
                else:
                    diag_entry["cache_hit"] = False
                    try:
                        temp_dest = dest_path.with_suffix(".tmp.jpg")
                        self.image_provider.generate_image(
                            prompt=prompt,
                            output_path=temp_dest,
                            width=576,
                            height=1024,
                        )
                        # Save to cache
                        self.asset_cache.save_to_cache(
                            prompt_hash=prompt_hash,
                            image_source_path=temp_dest,
                            prompt=prompt,
                            model=getattr(self.image_provider, "model", "flux"),
                            visual_style=visual_style,
                            width=576,
                            height=1024,
                        )
                        shutil.move(temp_dest, dest_path)
                        scene_source = "ai"
                        match_quality = "ai_generated"
                    except Exception as gen_err:
                        logger.warning(
                            f"AI image generation failed for scene {story_scene.order}: {gen_err}. "
                            "Executing rock-solid fallback to LocalAssetProvider."
                        )
                        diag_entry["error"] = str(gen_err)
                        diag_entry["fallback"] = "LocalAssetProvider"

                        # FALLBACK TO LOCAL STOCK ASSET
                        scene_context = f"{story_scene.visual_direction} {story_scene.narration} {visual_style}"
                        fallback_asset, _ = self.local_provider.catalog.select_best_asset(
                            visual_plan=visual_plan,
                            scene_text=scene_context,
                            domain=domain,
                            visual_style=visual_style,
                            previously_used=previously_used,
                        )
                        src_template = self.local_provider.templates_dir / fallback_asset.filename
                        if src_template.exists():
                            shutil.copy2(src_template, dest_path)
                        previously_used.append(fallback_asset.filename)
                        scene_source = "fallback_stock"
                        match_quality = "fallback_local"
            else:
                # Use local stock asset (from auto mode decision)
                scene_context = f"{story_scene.visual_direction} {story_scene.narration} {visual_style}"
                stock_asset, quality = self.local_provider.catalog.select_best_asset(
                    visual_plan=visual_plan,
                    scene_text=scene_context,
                    domain=domain,
                    visual_style=visual_style,
                    previously_used=previously_used,
                )
                src_template = self.local_provider.templates_dir / stock_asset.filename
                if src_template.exists():
                    shutil.copy2(src_template, dest_path)
                previously_used.append(stock_asset.filename)
                scene_source = "stock"
                match_quality = quality

            diag_entry["visual_source"] = scene_source
            diagnostics.append(diag_entry)

            # 4. Construct Scene object
            caption_words = [w.strip() for w in story_scene.caption.split() if w.strip()]
            emphasis = [caption_words[0]] if caption_words else []
            caption_segment = CaptionSegment(
                text=story_scene.caption,
                start_time=0.0,
                end_time=story_scene.estimated_duration,
                emphasis_words=emphasis,
                style="bold_pill",
            )

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
                caption_segments=story_scene.caption_segments or [caption_segment],
                motion=visual_plan.motion,
                transition=visual_plan.transition,
                visual_source=scene_source,
                alignment_source="estimated",
            )
            result_scenes.append(scene)

        self.last_diagnostics = diagnostics
        return result_scenes

    def regenerate_single_scene_visual(
        self,
        scene: Scene,
        visual_style: str,
        project_id: str,
        custom_prompt: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> tuple[Scene, dict]:
        """
        Regenerates ONLY the visual image for a single scene without modifying
        narration, captions, scene order, or other scenes.
        """
        project_dir = get_project_dir(project_id)
        visual_plan = scene.visual_plan or VisualPlanningEngine.plan_scene_visuals(scene=scene, visual_style=visual_style)
        scene.visual_plan = visual_plan

        dest_filename = f"scene_{scene.order}.jpg"
        dest_path = project_dir / dest_filename

        prompt = custom_prompt or VisualPromptBuilder.build_prompt(
            visual_plan=visual_plan,
            visual_style=visual_style,
            narration=scene.narration,
            scene_role=scene.scene_role or "insight",
        )

        diag: dict = {
            "scene_order": scene.order,
            "regenerated": True,
            "prompt": prompt,
            "seed": seed,
        }

        try:
            temp_dest = dest_path.with_suffix(f".regen_{int(time.time())}.jpg")
            self.image_provider.generate_image(
                prompt=prompt,
                output_path=temp_dest,
                width=576,
                height=1024,
                seed=seed,
            )
            shutil.move(temp_dest, dest_path)
            scene.visual_source = "ai"
            scene.match_quality = "ai_regenerated"
            diag["visual_source"] = "ai"
            diag["status"] = "success"
        except Exception as err:
            logger.warning(f"Regeneration via AI failed for scene {scene.order}: {err}. Falling back to stock.")
            diag["error"] = str(err)
            diag["fallback"] = "LocalAssetProvider"

            # Fallback to local stock asset
            stock_asset, _ = self.local_provider.catalog.select_best_asset(
                visual_plan=visual_plan,
                scene_text=f"{scene.visual_direction} {scene.narration} {visual_style}",
                domain="technology",
                visual_style=visual_style,
                previously_used=[],
            )
            src_template = self.local_provider.templates_dir / stock_asset.filename
            if src_template.exists():
                shutil.copy2(src_template, dest_path)
            scene.visual_source = "fallback_stock"
            scene.match_quality = "fallback_local"
            diag["visual_source"] = "fallback_stock"

        # Bust browser cache with timestamp query param in URL
        scene.visual_filename = dest_filename
        scene.visual_url = f"/media/uploads/{project_id}/{dest_filename}?v={int(time.time())}"

        return scene, diag


# Singletons
local_visual_provider = LocalAssetProvider()
smart_visual_provider = SmartVisualProvider()
