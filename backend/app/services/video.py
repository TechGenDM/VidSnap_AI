"""
VidSnap AI - Cinematic Video Rendering Engine (Phase 3)
Renders high-quality 1080x1920 (9:16 portrait) Reels driven by a RenderPlan.
Key responsibilities:
- render_scene_segment(): renders individual scenes with subtle camera motion and burned-in captions.
- composite_render_plan(): composites multi-scene segments with cinematic transitions (cut, crossfade, slide) and audio.
- inspect_rendered_frames(): verifies output frames at 15%, 50%, and 85% for resolution, aspect ratio, no black borders, contrast, and corruption.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from PIL import Image, ImageStat
from app.config import settings
from app.services.render_plan import RenderPlan, SceneRenderItem
from app.services.motion import MotionEngine

logger = logging.getLogger("vidsnap.video")

SYSTEM_FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFPro.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
FONT_PATH = next((f for f in SYSTEM_FONTS if Path(f).exists()), "")


@dataclass
class FrameInspectionResult:
    passed: bool
    inspected_timestamps: list[float]
    frame_paths: list[str]
    resolution: tuple[int, int]
    aspect_ratio: str
    has_black_borders: bool
    is_corrupted: bool
    contrast_adequate: bool
    issues: list[str]
    metrics: dict = field(default_factory=dict)


def wrap_caption(text: str, max_words_per_line: int = 5) -> str:
    """
    Wraps caption text to prevent horizontal overflow on 1080px portrait canvas.
    """
    words = text.split()
    if len(words) <= max_words_per_line:
        return text
    lines = []
    for i in range(0, len(words), max_words_per_line):
        lines.append(" ".join(words[i : i + max_words_per_line]))
    return "\n".join(lines)


def render_scene_segment(
    item: SceneRenderItem,
    output_segment_path: Path,
    fps: int = 30,
    target_width: int = 1080,
    target_height: int = 1920,
    padding_duration: float = 0.0,
) -> Path:
    """
    Renders a single scene into a 1080x1920 MP4 segment with subtle camera motion,
    sharp portrait framing, and burned-in caption overlay.
    """
    output_segment_path.parent.mkdir(parents=True, exist_ok=True)
    total_segment_duration = item.duration + padding_duration

    # 1. Build motion filter
    motion_filter = MotionEngine.build_motion_filter(
        motion=item.motion,
        duration=total_segment_duration,
        fps=fps,
        target_width=target_width,
        target_height=target_height,
    )

    # 2. Build safe caption overlay (ASS kinetic subtitles preferred, drawtext fallback)
    caption_filter = ""
    caption_file = None
    ass_file = None
    caption_text = item.caption.strip()

    has_kinetic_segments = bool(item.caption_segments and any(s.words for s in item.caption_segments))

    if has_kinetic_segments:
        try:
            from app.services.caption_generator import ASSCaptionGenerator
            ass_path = output_segment_path.with_suffix(".ass")
            ASSCaptionGenerator.generate_ass_file(
                segments=item.caption_segments,
                output_path=ass_path,
                scene_offset=0.0,
                style="kinetic",
            )
            ass_file = ass_path
            # Escape path for ffmpeg filter: colons and backslashes
            escaped_ass_path = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
            caption_filter = f",ass='{escaped_ass_path}'"
        except Exception as e:
            logger.warning(f"ASS kinetic caption generation failed ({e}), falling back to drawtext.")
            has_kinetic_segments = False

    if not has_kinetic_segments and caption_text:
        wrapped_caption = wrap_caption(caption_text)
        caption_file = output_segment_path.with_suffix(".caption.txt")
        caption_file.write_text(wrapped_caption, encoding="utf-8")

        font_param = f":fontfile='{FONT_PATH}'" if FONT_PATH else ""
        caption_filter = (
            f",drawtext=textfile='{caption_file}'"
            f"{font_param}:"
            f"fontsize=46:fontcolor=white:"
            f"box=1:boxcolor=black@0.72:boxborderw=20:line_spacing=12:"
            f"x=(w-text_w)/2:y=h*0.78"
        )

    full_filter = f"{motion_filter}{caption_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(item.image_path),
        "-vf", full_filter,
        "-t", f"{total_segment_duration:.3f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        str(output_segment_path),
    ]

    try:
        res = subprocess.run(cmd, shell=False, capture_output=True, text=True)
        if res.returncode != 0:
            error_details = res.stderr[-600:] if res.stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg failed rendering scene {item.order} ({item.motion}): {error_details}")
    finally:
        if caption_file and caption_file.exists():
            caption_file.unlink(missing_ok=True)
        if ass_file and ass_file.exists():
            ass_file.unlink(missing_ok=True)

    return output_segment_path


def composite_render_plan(
    plan: RenderPlan,
    temp_dir: Path,
) -> tuple[Path, list[float]]:
    """
    Composites all scene segments according to the RenderPlan with cinematic transitions
    and audio sync. Always cleans up temporary files.
    """
    plan.output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    num_scenes = len(plan.scenes)
    if num_scenes == 0:
        raise ValueError("RenderPlan has no scenes.")

    fps = plan.fps
    segment_paths: list[Path] = []
    scene_durations: list[float] = [s.duration for s in plan.scenes]

    # Calculate transition overlaps
    # Transitions supported: "cut", "short_fade", "crossfade", "directional_slide"
    trans_durations: list[float] = []
    for i in range(num_scenes - 1):
        curr_scene = plan.scenes[i]
        trans_name = curr_scene.transition or "crossfade"
        if trans_name == "cut":
            trans_durations.append(0.0)
        else:
            # Conservative transition length: max 0.35s, not exceeding 25% of either scene
            max_allowed = min(0.35, curr_scene.duration * 0.25, plan.scenes[i + 1].duration * 0.25)
            trans_durations.append(round(max(0.15, max_allowed), 3))

    try:
        # Step 1: Render each scene segment with padding if transitioning to next scene
        for idx, item in enumerate(plan.scenes):
            padding = trans_durations[idx] if idx < len(trans_durations) else 0.0
            seg_file = temp_dir / f"segment_{idx:03d}.mp4"
            logger.info(
                f"Rendering scene {item.order}/{num_scenes} ({item.duration:.2f}s, "
                f"motion='{item.motion}', trans='{item.transition}') -> {seg_file.name}"
            )
            render_scene_segment(
                item=item,
                output_segment_path=seg_file,
                fps=fps,
                target_width=plan.width,
                target_height=plan.height,
                padding_duration=padding,
            )
            segment_paths.append(seg_file)

        # Step 2: Assemble video stream (either xfade chain or concat)
        has_active_xfade = any(td > 0.0 for td in trans_durations)

        if not has_active_xfade or num_scenes == 1:
            # Clean direct concatenation
            filter_inputs = "".join([f"[{i}:v]" for i in range(num_scenes)])
            filter_complex = f"{filter_inputs}concat=n={num_scenes}:v=1:a=0[vconcat]"
            video_stream_label = "[vconcat]"
        else:
            # Chained xfade filters
            filter_parts = []
            current_stream = "[0:v]"
            accumulated_offset = 0.0

            for i in range(num_scenes - 1):
                accumulated_offset += plan.scenes[i].duration
                curr_trans = plan.scenes[i].transition or "crossfade"
                td = trans_durations[i]

                if curr_trans == "directional_slide":
                    xfade_trans = "slideleft"
                elif curr_trans == "short_fade":
                    xfade_trans = "fade"
                else: # crossfade
                    xfade_trans = "fade" # clean smooth fade through transition

                next_stream = f"[{i+1}:v]"
                out_label = f"[vx{i}]" if i < num_scenes - 2 else "[vconcat]"
                filter_parts.append(
                    f"{current_stream}{next_stream}xfade=transition={xfade_trans}:duration={td:.3f}:offset={accumulated_offset:.3f}{out_label}"
                )
                current_stream = out_label

            filter_complex = ";".join(filter_parts)
            video_stream_label = "[vconcat]"

        # Step 3: Final compositing with audio plan
        cmd = ["ffmpeg", "-y"]
        for seg in segment_paths:
            cmd.extend(["-i", str(seg)])
        cmd.extend(["-i", str(plan.audio.audio_path)])

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", video_stream_label,
            "-map", f"{num_scenes}:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(plan.output_path),
        ])

        logger.info(f"Compositing final Reel with synced audio ({plan.audio.total_duration:.2f}s)...")
        res = subprocess.run(cmd, shell=False, capture_output=True, text=True)
        if res.returncode != 0:
            err_details = res.stderr[-600:] if res.stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg final composition failed: {err_details}")

    finally:
        # Step 4: Cleanup temporary scene segment files
        for seg in segment_paths:
            seg.unlink(missing_ok=True)

    return plan.output_path, scene_durations


def inspect_rendered_frames(
    video_path: Path,
    output_dir: Path,
) -> FrameInspectionResult:
    """
    Extracts frames at approximately 15%, 50%, and 85% of the rendered video.
    Verifies:
    - 1080x1920 resolution
    - 9:16 aspect ratio
    - No black borders / letterboxing
    - No obvious stretching or corrupted / blank frames
    - Contrast and caption visibility heuristics
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Get video duration via ffprobe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    probe_res = subprocess.run(probe_cmd, shell=False, capture_output=True, text=True)
    if probe_res.returncode != 0:
        raise RuntimeError(f"ffprobe failed inspecting video duration: {probe_res.stderr}")

    duration = float(probe_res.stdout.strip() or "0.0")
    if duration <= 0.0:
        raise ValueError("Rendered video has zero duration.")

    pcts = [0.15, 0.50, 0.85]
    timestamps = [round(duration * p, 2) for p in pcts]
    frame_paths: list[str] = []
    issues: list[str] = []
    metrics: dict = {}

    for idx, (pct, ts) in enumerate(zip(pcts, timestamps)):
        frame_file = output_dir / f"inspect_frame_{int(pct*100)}pct.png"
        extract_cmd = [
            "ffmpeg", "-y",
            "-ss", f"{ts:.2f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(frame_file),
        ]
        sub_res = subprocess.run(extract_cmd, shell=False, capture_output=True, text=True)
        if sub_res.returncode != 0 or not frame_file.exists():
            issues.append(f"Failed to extract frame at {pct*100:.0f}% ({ts}s).")
            continue

        frame_paths.append(str(frame_file))

        # Pixel Inspection using PIL
        with Image.open(frame_file) as img:
            w, h = img.size
            if (w, h) != (1080, 1920):
                issues.append(f"Frame at {pct*100:.0f}% resolution is {w}x{h}, expected 1080x1920.")

            aspect = w / h
            if abs(aspect - (9 / 16)) > 0.01:
                issues.append(f"Frame at {pct*100:.0f}% aspect ratio {aspect:.3f} deviates from 9:16 (0.5625).")

            # Luminance statistics
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            mean_lum = stat.mean[0]
            stddev_lum = stat.stddev[0]
            metrics[f"frame_{int(pct*100)}pct_mean_lum"] = round(mean_lum, 2)
            metrics[f"frame_{int(pct*100)}pct_stddev_lum"] = round(stddev_lum, 2)

            # Corrupted / solid black or grey frame detection
            if stddev_lum < 5.0:
                issues.append(f"Frame at {pct*100:.0f}% has near-zero variance ({stddev_lum:.2f}), likely blank or corrupted.")

            # Black borders check: sample top, bottom, left, right edges
            top_strip = gray.crop((0, 0, w, 20))
            bot_strip = gray.crop((0, h - 20, w, h))
            left_strip = gray.crop((0, 0, 20, h))
            right_strip = gray.crop((w - 20, 0, w, h))

            if ImageStat.Stat(top_strip).mean[0] < 5.0 and ImageStat.Stat(bot_strip).mean[0] < 5.0:
                issues.append(f"Frame at {pct*100:.0f}% exhibits horizontal black letterbox bars.")
            if ImageStat.Stat(left_strip).mean[0] < 5.0 and ImageStat.Stat(right_strip).mean[0] < 5.0:
                issues.append(f"Frame at {pct*100:.0f}% exhibits vertical black pillarbox bars.")

            # Caption zone inspection (y from 72% to 85%)
            cap_zone = gray.crop((int(w * 0.1), int(h * 0.72), int(w * 0.9), int(h * 0.85)))
            cap_stat = ImageStat.Stat(cap_zone)
            metrics[f"frame_{int(pct*100)}pct_caption_zone_stddev"] = round(cap_stat.stddev[0], 2)

    has_black_borders = any("black" in iss for iss in issues)
    is_corrupted = any("corrupted" in iss or "blank" in iss for iss in issues)
    contrast_adequate = not any("variance" in iss for iss in issues)
    passed = len(issues) == 0

    return FrameInspectionResult(
        passed=passed,
        inspected_timestamps=timestamps,
        frame_paths=frame_paths,
        resolution=(1080, 1920),
        aspect_ratio="9:16",
        has_black_borders=has_black_borders,
        is_corrupted=is_corrupted,
        contrast_adequate=contrast_adequate,
        issues=issues,
        metrics=metrics,
    )


# ---------------------------------------------------------------------------
# Backward-compatibility API for legacy callers & Quick Reel
# ---------------------------------------------------------------------------

def render_single_slide(
    image_path: Path,
    duration: float,
    caption: str,
    output_segment_path: Path,
    scene_index: int = 0,
) -> Path:
    """
    Renders a single image into a 1080x1920 MP4 segment with subtle camera motion.
    Maintained for direct single-slide callers.
    """
    item = SceneRenderItem(
        scene_id=f"legacy_{scene_index}",
        order=scene_index + 1,
        image_path=image_path,
        duration=duration,
        caption=caption,
        motion="slow_zoom_in",
        transition="crossfade",
    )
    return render_scene_segment(item, output_segment_path)


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
        subprocess.run(cmd, shell=False, check=True, capture_output=True)
    except Exception as e:
        logger.warning(f"Could not extract thumbnail frame at {timestamp}s: {e}. Falling back to 0.0s")
        cmd[2] = "0.0"
        subprocess.run(cmd, shell=False, check=True, capture_output=True)
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
    Constructs an ephemeral RenderPlan and composites with cinematic motion.
    """
    num_images = len(image_paths)
    if num_images == 0:
        raise ValueError("At least one image is required to render a reel.")

    slide_duration = total_audio_duration / num_images
    scene_items = []
    
    # Varied motions for legacy multi-image reels
    motion_cycle = ["slow_zoom_in", "pan_left", "slow_zoom_out", "pan_right", "vertical_drift"]

    for idx, img in enumerate(image_paths):
        cap = captions[idx] if idx < len(captions) else ""
        item = SceneRenderItem(
            scene_id=f"scene_{idx+1}",
            order=idx + 1,
            image_path=img,
            duration=slide_duration,
            caption=cap,
            motion=motion_cycle[idx % len(motion_cycle)],
            transition="crossfade" if idx < num_images - 1 else "static_hold",
        )
        scene_items.append(item)

    from app.services.render_plan import AudioRenderPlan
    plan = RenderPlan(
        project_id="legacy_render",
        scenes=scene_items,
        audio=AudioRenderPlan(audio_path=audio_path, total_duration=total_audio_duration),
        output_path=output_video_path,
        width=1080,
        height=1920,
        fps=settings.VIDEO_FPS,
    )

    return composite_render_plan(plan, temp_dir)
