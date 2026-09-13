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

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-t", f"{duration:.3f}",
        "-i", str(image_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        str(output_segment_path),
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_segment_path

def generate_video_thumbnail(video_path: Path, thumbnail_path: Path, timestamp: float = 0.5) -> Path:
    """
    Extracts a crisp thumbnail frame from the rendered MP4 for project cards and previews.
    """
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{timestamp:.2f}",
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(thumbnail_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception as e:
        logger.warning(f"Could not extract thumbnail frame at {timestamp}s: {e}. Falling back to 0.0s")
        cmd[2] = "0.0"
        subprocess.run(cmd, check=True, capture_output=True)
    return thumbnail_path

def render_reel_video(
    image_paths: list[Path],
    audio_path: Path,
    captions: list[str],
    total_audio_duration: float,
    output_video_path: Path,
    temp_dir: Path,
) -> tuple[Path, list[float]]:
    """
    Renders complete 1080x1920 vertical Reel synced to the exact audio duration.
    Calculates dynamic timing for each scene.
    Returns: (output_video_path, list_of_scene_durations)
    """
    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    num_images = len(image_paths)
    if num_images == 0:
        raise ValueError("At least one image is required to render a reel.")

    # Dynamic Scene Durations
    # Divide audio duration evenly across all slides
    slide_duration = total_audio_duration / num_images
    scene_durations = [slide_duration] * num_images

    segment_paths = []
    for idx, img_path in enumerate(image_paths):
        caption = captions[idx] if idx < len(captions) else ""
        segment_file = temp_dir / f"segment_{idx:03d}.mp4"
        logger.info(f"Rendering slide {idx + 1}/{num_images} ({slide_duration:.2f}s) for {img_path.name}...")
        render_single_slide(
            image_path=img_path,
            duration=slide_duration,
            caption=caption,
            output_segment_path=segment_file,
            scene_index=idx,
        )
        segment_paths.append(segment_file)

    # Concat segments using concat filter (frame-accurate and seamless)
    filter_inputs = "".join([f"[{i}:v]" for i in range(num_images)])
    filter_complex = f"{filter_inputs}concat=n={num_images}:v=1:a=0[vconcat]"

    cmd = ["ffmpeg", "-y"]
    for seg in segment_paths:
        cmd.extend(["-i", str(seg)])
    cmd.extend(["-i", str(audio_path)])

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vconcat]",
        "-map", f"{num_images}:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_video_path),
    ])

    logger.info(f"Compositing final Reel with synced audio ({total_audio_duration:.2f}s)...")
    subprocess.run(cmd, check=True, capture_output=True)

    # Cleanup intermediate segment files
    for seg in segment_paths:
        seg.unlink(missing_ok=True)

    return output_video_path, scene_durations
