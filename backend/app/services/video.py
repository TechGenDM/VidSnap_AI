import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger("vidsnap.video")

def render_single_slide(
    image_path: Path,
    duration: float,
    caption: str,
    output_segment_path: Path,
    scene_index: int = 0,
) -> Path:
    """
    Renders a single image into a 1080x1920 MP4 segment with blurred background framing,
    crisp centered foreground, normalized SAR 1:1, and burned-in clean caption text.
    """
    output_segment_path.parent.mkdir(parents=True, exist_ok=True)
    fps = settings.VIDEO_FPS

