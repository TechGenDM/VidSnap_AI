import shutil
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models import Scene, StoryScene
from app.services.storage import get_project_dir

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
    ) -> list[Scene]:
        """Maps story scenes to concrete visual assets for rendering."""
        pass


class LocalAssetProvider(VisualProvider):
    """
    Local Asset Provider matching story scenes with available local stock/template photography.
    Does not pretend an AI-generated image exists when it was not generated.
    Copies designated assets to the project upload directory to ensure self-contained project storage.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR

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
    ) -> list[Scene]:
        project_dir = get_project_dir(project_id)
        templates = self._get_available_templates()

        if not templates:
            logger.warning(f"No templates found in {self.templates_dir}. Creating emergency visual fallback.")
            # Create a simple solid canvas as fallback if templates are somehow deleted
            from PIL import Image
            fallback_img = project_dir / "fallback.jpg"
            img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
            img.save(fallback_img, "JPEG")
            templates = [fallback_img]

        result_scenes: list[Scene] = []
        for idx, story_scene in enumerate(scenes):
            # Deterministic selection based on scene order and total available templates
            src_template = templates[idx % len(templates)]
            dest_filename = f"scene_{story_scene.order}.jpg"
            dest_path = project_dir / dest_filename

            # Copy template to project uploads folder
            try:
                shutil.copy2(src_template, dest_path)
            except Exception as e:
                logger.error(f"Failed copying template {src_template} to {dest_path}: {e}")

            scene = Scene(
                id=f"scene_{story_scene.order}",
                order=story_scene.order,
                visual_filename=dest_filename,
                visual_url=f"/media/uploads/{project_id}/{dest_filename}",
                visual_direction=story_scene.visual_direction,
                narration=story_scene.narration,
                caption=story_scene.caption,
                duration_seconds=story_scene.estimated_duration,
            )
            result_scenes.append(scene)

        return result_scenes

local_visual_provider = LocalAssetProvider()
