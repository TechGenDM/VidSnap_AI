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


TEMPLATE_SEMANTICS = {
    "1.jpg": ["code", "developer", "ide", "laptop", "typing", "syntax", "editor", "terminal", "dark", "minimal"],
    "2.jpg": ["architecture", "flowchart", "network", "system", "nodes", "graph", "microservices", "infrastructure", "abstract", "connected"],
    "3.jpg": ["creator", "lifestyle", "coffee", "desk", "clean", "workspace", "founder", "minimalist", "office", "laptop"],
    "4.jpg": ["dashboard", "metrics", "analytics", "growth", "graph", "screen", "charts", "launch", "velocity", "data"],
    "5.jpg": ["city", "horizon", "future", "modern", "night", "buildings", "global", "connected", "lights", "skyline"],
}

class LocalAssetProvider(VisualProvider):
    """
    Local Asset Provider matching story scenes with available local stock/template photography.
    Scores semantic relevance against template metadata.
    Enforces visual variety by preventing consecutive duplicates across scenes.
    Exposes whether a match is exact or approximate without claiming false AI comprehension.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR

    def _get_available_templates(self) -> list[Path]:
        if not self.templates_dir.exists():
            return []
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        files = sorted([f for f in self.templates_dir.iterdir() if f.suffix.lower() in valid_exts])
        return files

    def _score_template(self, template_path: Path, scene_text: str) -> int:
        tags = TEMPLATE_SEMANTICS.get(template_path.name, [])
        text_lower = scene_text.lower()
        score = sum(1 for tag in tags if tag in text_lower)
        return score

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
            from PIL import Image
            fallback_img = project_dir / "fallback.jpg"
            img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
            img.save(fallback_img, "JPEG")
            templates = [fallback_img]

        result_scenes: list[Scene] = []
        last_chosen_name: Optional[str] = None

        for idx, story_scene in enumerate(scenes):
            scene_context = f"{story_scene.visual_direction} {story_scene.narration} {visual_style}"
            
            # Score each template
            scored_candidates = []
            for tmpl in templates:
                s = self._score_template(tmpl, scene_context)
                scored_candidates.append((s, tmpl))

            # Sort descending by score
            scored_candidates.sort(key=lambda x: x[0], reverse=True)

            # Pick best template that is NOT identical to the previous scene (variety)
            chosen_tuple = None
            for score, tmpl in scored_candidates:
                if tmpl.name != last_chosen_name or len(templates) == 1:
                    chosen_tuple = (score, tmpl)
                    break
            
            if not chosen_tuple:
                chosen_tuple = scored_candidates[0]

            score, src_template = chosen_tuple
            last_chosen_name = src_template.name
            dest_filename = f"scene_{story_scene.order}.jpg"
            dest_path = project_dir / dest_filename

            # Determine match quality
            match_quality = "exact" if score >= 2 else "approximate"

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
                scene_role=story_scene.scene_role,
                match_quality=match_quality,
            )
            result_scenes.append(scene)

        return result_scenes

local_visual_provider = LocalAssetProvider()
