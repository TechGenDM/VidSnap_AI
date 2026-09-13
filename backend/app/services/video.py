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

    # Sanitize caption for FFmpeg drawtext
    clean_caption = caption.replace("'", "").replace(":", " - ").replace("\\", "").strip()

    caption_filter = ""
    if clean_caption:
        caption_filter = (
            f",drawtext=text='{clean_caption}':"
            f"fontsize=42:fontcolor=white:"
            f"box=1:boxcolor=black@0.65:boxborderw=18:"
            f"x=(w-text_w)/2:y=h*0.78"
        )

    filter_complex = (
        f"[0:v]split=2[v1][v2];"
        f"[v1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:5[bg];"
        f"[v2]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"
        f"{caption_filter}[vout]"
    )

