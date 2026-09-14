"""
VidSnap AI - Image Generation & Asset Caching Architecture (Phase 4)
Integrates real AI image generation via Pollinations current API architecture (https://gen.pollinations.ai).

Supports:
- ImageGenerationProvider interface
- PollinationsImageProvider with live model selection, API key authentication, retries, and PIL validation
- VisualPromptBuilder with project-level visual consistency (color_language, cinematic_style, subject_anchor)
- Strict vertical 9:16 portrait prompt construction (no text, no logos/watermarks)
- Deterministic asset caching by normalized hash: prompt + model + aspect_ratio + style + seed
- Graceful error raising for LocalAssetProvider fallback
"""

import io
import json
import time
import hashlib
import logging
import urllib.request
import urllib.parse
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from PIL import Image

from app.config import settings
from app.models import VisualPlan

logger = logging.getLogger("vidsnap.services.image_generation")


class ImageGenerationError(Exception):
    """Raised when an external image generation provider fails."""
    pass


class ImageGenerationProvider(ABC):
    """
    Abstract interface for image generation providers (Pollinations, future OpenAI DALL-E, etc.).
    """

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        width: int = 576,
        height: int = 1024,
        seed: Optional[int] = None,
    ) -> Path:
        """Generates an image from prompt and writes it to output_path."""
        pass


class PollinationsImageProvider(ImageGenerationProvider):
    """
    Real Image Generation Provider using current Pollinations API (https://gen.pollinations.ai).
    Supports authenticated API key flow (POLLINATIONS_API_KEY) and configurable image model (POLLINATIONS_IMAGE_MODEL).
    Includes timeouts, retries, response verification, and PIL validation.
    """

    BASE_URL = "https://gen.pollinations.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 25,
    ):
        self.api_key = api_key if api_key is not None else settings.POLLINATIONS_API_KEY
        self.model = model or settings.POLLINATIONS_IMAGE_MODEL or "flux"
        self.timeout = timeout

    @classmethod
    def validate_image_file(cls, file_path: Path, min_dim: int = 100) -> Path:
        """Validates an existing image file using PIL, verifying it is uncorrupted and of adequate dimensions."""
        if not file_path.exists():
            raise ImageGenerationError(f"Image file does not exist: {file_path}")
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            img = Image.open(io.BytesIO(data))
            img.verify()
            img = Image.open(io.BytesIO(data))
            w, h = img.size
            if w < min_dim or h < min_dim:
                raise ImageGenerationError(f"Image dimensions too small ({w}x{h}, minimum {min_dim}px)")
            return file_path
        except Exception as e:
            raise ImageGenerationError(f"Invalid or corrupt image: {e}")

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        width: int = 576,
        height: int = 1024,
        seed: Optional[int] = None,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize prompt for URL safety: eliminate colons to avoid route ambiguity
        safe_prompt = prompt.replace(":", " - ").strip()
        encoded_prompt = urllib.parse.quote(safe_prompt)

        # Build query parameters
        params = {
            "model": self.model,
            "width": str(width),
            "height": str(height),
            "nologo": "true",
        }
        if seed is not None:
            params["seed"] = str(seed)
        if self.api_key:
            params["key"] = self.api_key

        query_str = urllib.parse.urlencode(params)
        req_url = f"{self.BASE_URL}/image/{encoded_prompt}?{query_str}"

        headers = {
            "User-Agent": "VidSnapAI/2.0 (Short-form video creation platform)",
            "Accept": "image/jpeg, image/png, image/*",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info(f"Requesting AI image from {self.BASE_URL} (Model: {self.model}, {width}x{height})...")

        last_error = None
        max_retries = 2

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(req_url, headers=headers)
                t0 = time.time()
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "")
                    data = resp.read()

                    if status != 200 or not data:
                        raise ImageGenerationError(f"Pollinations API returned status {status} with empty payload")

                    # Validate with PIL
                    try:
                        img = Image.open(io.BytesIO(data))
                        img.verify()
                        # Re-open after verify to ensure image can be read/saved
                        img = Image.open(io.BytesIO(data))
                        img_w, img_h = img.size
                        if img_w < 100 or img_h < 100:
                            raise ImageGenerationError(f"Generated image dimensions too small ({img_w}x{img_h})")
                        
                        # Save directly as clean JPEG
                        img.convert("RGB").save(output_path, "JPEG", quality=92)
                        elapsed = time.time() - t0
                        logger.info(f"AI image generated and validated successfully in {elapsed:.2f}s ({img_w}x{img_h}) -> {output_path.name}")
                        return output_path
                    except Exception as pil_err:
                        raise ImageGenerationError(f"PIL validation failed on Pollinations response: {pil_err}")

            except urllib.error.HTTPError as http_err:
                error_body = ""
                try:
                    error_body = http_err.read().decode("utf-8", errors="ignore")[:250]
                except Exception:
                    pass

                last_error = f"HTTP {http_err.code} {http_err.reason}: {error_body}"
                logger.warning(f"Pollinations generation attempt {attempt} failed: {last_error}")

                if http_err.code in (401, 403):
                    # Authentication failure: fail immediately without useless retries
                    raise ImageGenerationError(f"Pollinations authentication error ({last_error}). Verify POLLINATIONS_API_KEY.")
                if attempt < max_retries:
                    time.sleep(1.5 * attempt)

            except Exception as net_err:
                last_error = str(net_err)
                logger.warning(f"Pollinations generation network attempt {attempt} failed: {last_error}")
                if attempt < max_retries:
                    time.sleep(1.5 * attempt)

        raise ImageGenerationError(f"Failed generating AI visual after {max_retries} attempts: {last_error}")


class VisualPromptBuilder:
    """
    Constructs high-aesthetic, cinematic 9:16 vertical image prompts from VisualPlan,
    story context, and project-level visual consistency configuration.
    Never sends raw narration directly to the image model.
    """

    STYLE_CONFIGS = {
        "cinematic tech": {
            "color_language": "deep midnight blue, slate obsidian, cool ambient backlight, subtle electric cyan accents",
            "cinematic_style": "cinematic 35mm film still, anamorphic framing, clean shallow depth of field, sharp edge highlights",
            "subject_anchor": "software engineer in modern dark tech apparel directing autonomous intelligent systems",
        },
        "minimal tech": {
            "color_language": "clean monochrome palette, matte graphite, soft diffused white lighting, minimalist accents",
            "cinematic_style": "contemporary editorial photography, high dynamic range, architectural symmetry",
            "subject_anchor": "minimalist developer workspace with modern workstation displays",
        },
        "warm documentary": {
            "color_language": "warm amber tones, rich walnut wood, soft natural golden hour illumination",
            "cinematic_style": "documentary cinematic portrait, natural 50mm perspective, filmic grain",
            "subject_anchor": "thoughtful creator reflecting in an authentic modern studio environment",
        },
        "dynamic": {
            "color_language": "high-contrast vibrant neon highlights, rich shadows, vivid energetic saturation",
            "cinematic_style": "fast-paced modern editorial, sharp macro focus, dramatic directional rim lighting",
            "subject_anchor": "innovator actively orchestrating complex technological solutions",
        },
    }

    @classmethod
    def get_style_context(cls, visual_style: str) -> dict:
        norm = visual_style.strip().lower()
        for k, v in cls.STYLE_CONFIGS.items():
            if k in norm:
                return v
        return cls.STYLE_CONFIGS["cinematic tech"]

    @classmethod
    def build_prompt(
        cls,
        visual_plan: VisualPlan,
        visual_style: str = "Cinematic Tech",
        narration: str = "",
        scene_role: str = "insight",
    ) -> str:
        """
        Builds a complete, deterministic, portrait-optimized image prompt.
        """
        style_ctx = cls.get_style_context(visual_style)
        color_lang = style_ctx["color_language"]
        cinematic_style = style_ctx["cinematic_style"]

        # Synthesize visual components
        subject = visual_plan.subject or style_ctx["subject_anchor"]
        environment = visual_plan.environment or "modern architecture workstation"
        visual_type = visual_plan.visual_type.replace("_", " ") if visual_plan.visual_type else "workstation scene"
        composition = visual_plan.composition.replace("_", " ") if visual_plan.composition else "medium wide angle"
        mood = visual_plan.mood or "focused and progressive"
        emphasis = visual_plan.emphasis or "intelligent software orchestration"

        # Build structured positive prompt
        prompt_parts = [
            f"{cinematic_style}",
            f"{visual_type} set in {environment}",
            f"showing {subject}",
            f"emphasizing {emphasis}",
            f"{composition}",
            f"{mood} atmosphere",
            f"color palette of {color_lang}",
            "photorealistic, masterwork detail, 8k resolution, crisp focus",
            "vertical 9:16 portrait composition, tailored for mobile vertical screen framing",
            # Mandatory negative constraints
            "no text, no typography, no watermarks, no logos, no distorted interface elements, no unreadable UI artifacts"
        ]

        full_prompt = ", ".join(prompt_parts)
        return full_prompt


class AssetCache:
    """
    Manages local filesystem caching of AI-generated assets keyed by normalized configuration hash.
    Prevents duplicate generation calls and provides full diagnostic metadata.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.AI_ASSETS_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def compute_hash(
        cls,
        prompt: str,
        model: str,
        width: int,
        height: int,
        visual_style: str,
        seed: Optional[int] = None,
    ) -> str:
        """
        Computes a deterministic SHA-256 hash of the complete generation parameters.
        """
        raw_key = f"{prompt.strip().lower()}|{model.strip().lower()}|{width}x{height}|{visual_style.strip().lower()}|{seed}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]

    def get_cached_image(self, prompt_hash: str) -> Optional[Path]:
        img_path = self.cache_dir / f"{prompt_hash}.jpg"
        if img_path.exists() and img_path.stat().st_size > 1000:
            return img_path
        return None

    def save_to_cache(
        self,
        prompt_hash: str,
        image_source_path: Path,
        prompt: str,
        model: str,
        visual_style: str,
        width: int,
        height: int,
        seed: Optional[int] = None,
        provider: str = "pollinations",
    ) -> Path:
        dest_img = self.cache_dir / f"{prompt_hash}.jpg"
        dest_meta = self.cache_dir / f"{prompt_hash}.json"

        # Copy image to cache
        import shutil
        if image_source_path.resolve() != dest_img.resolve():
            shutil.copy2(image_source_path, dest_img)

        # Write metadata
        metadata = {
            "provider": provider,
            "model": model,
            "prompt_hash": prompt_hash,
            "prompt": prompt,
            "visual_style": visual_style,
            "width": width,
            "height": height,
            "seed": seed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "ai",
        }
        dest_meta.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return dest_img


# Default singletons
default_image_provider = PollinationsImageProvider()
default_asset_cache = AssetCache()
