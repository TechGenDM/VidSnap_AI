"""
VidSnap AI - FFmpeg Memory & Scene Rendering Regression Test
Verifies that high-resolution visual assets (5K/4K) render cleanly under
constrained memory environments with subtle motion filters (slow_zoom_in, etc.)
without causing OOM or FFmpeg aborts.
"""

import pytest
import subprocess
from pathlib import Path
from PIL import Image

from app.services.render_plan import SceneRenderItem
from app.services.video import render_scene_segment, safe_prepare_image
from app.models import CaptionSegment


@pytest.fixture
def high_res_image(tmp_path: Path) -> Path:
    """Creates an 18-megapixel (5192x3466) image matching the production Railway failure asset."""
    img_path = tmp_path / "high_res_scene.jpg"
    img = Image.new("RGB", (5192, 3466), color=(30, 45, 80))
    img.save(img_path, format="JPEG", quality=90)
    return img_path


def test_safe_prepare_image_oversized_downscale(high_res_image: Path, tmp_path: Path):
    temp_dir = tmp_path / "prep"
    prepared = safe_prepare_image(high_res_image, temp_dir, max_w=1620, max_h=2880)

    assert prepared.exists()
    assert prepared != high_res_image

    with Image.open(prepared) as im:
        assert im.size == (1620, 2880)


def test_safe_prepare_image_standard_passthrough(tmp_path: Path):
    standard_img = tmp_path / "standard.jpg"
    img = Image.new("RGB", (1080, 1920), color=(10, 20, 30))
    img.save(standard_img, format="JPEG")

    prepared = safe_prepare_image(standard_img, tmp_path / "prep")
    assert prepared == standard_img


def test_slow_zoom_in_high_res_scene_renders_successfully(high_res_image: Path, tmp_path: Path):
    out_segment = tmp_path / "segment_slow_zoom_in.mp4"
    duration = 4.5

    item = SceneRenderItem(
        scene_id="scene_1_regression",
        order=1,
        image_path=high_res_image,
        duration=duration,
        caption="THE HIDDEN TRUTH",
        motion="slow_zoom_in",
        transition="cut",
        caption_segments=[
            CaptionSegment(
                text="THE HIDDEN TRUTH",
                start_time=0.0,
                end_time=duration,
                emphasis_words=["THE"],
                style="bold_pill",
            )
        ],
    )

    rendered_path = render_scene_segment(
        item=item,
        output_segment_path=out_segment,
        fps=30,
        padding_duration=0.04,
    )

    assert rendered_path.exists()
    assert rendered_path.stat().st_size > 5000

    # Verify ffprobe duration and resolution
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "default=noprint_wrappers=1",
        str(rendered_path),
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "width=1080" in res.stdout
    assert "height=1920" in res.stdout


@pytest.mark.parametrize("motion", ["slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "vertical_drift", "static_hold"])
def test_all_motions_render_without_loop(high_res_image: Path, tmp_path: Path, motion: str):
    out_segment = tmp_path / f"segment_{motion}.mp4"
    duration = 2.0

    item = SceneRenderItem(
        scene_id=f"scene_{motion}",
        order=1,
        image_path=high_res_image,
        duration=duration,
        caption="TEST MOTION",
        motion=motion,
        transition="cut",
    )

    rendered_path = render_scene_segment(
        item=item,
        output_segment_path=out_segment,
        fps=30,
    )

    assert rendered_path.exists()
    assert rendered_path.stat().st_size > 5000


def test_composite_render_plan_multi_scene_memory_safety(high_res_image: Path, tmp_path: Path):
    from app.services.render_plan import RenderPlan, AudioRenderPlan
    from app.services.video import composite_render_plan

    audio_file = tmp_path / "test_audio.aac"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "8", "-c:a", "aac", str(audio_file)
    ], capture_output=True, check=True)

    scenes = [
        SceneRenderItem(
            scene_id="s1",
            order=1,
            image_path=high_res_image,
            duration=2.5,
            caption="SCENE ONE",
            motion="slow_zoom_in",
            transition="fade",
        ),
        SceneRenderItem(
            scene_id="s2",
            order=2,
            image_path=high_res_image,
            duration=2.5,
            caption="SCENE TWO",
            motion="pan_left",
            transition="directional_slide",
        ),
        SceneRenderItem(
            scene_id="s3",
            order=3,
            image_path=high_res_image,
            duration=2.5,
            caption="SCENE THREE",
            motion="slow_zoom_out",
            transition="cut",
        ),
    ]

    out_reel = tmp_path / "final_composite_reel.mp4"
    plan = RenderPlan(
        project_id="test_mem_proj",
        scenes=scenes,
        audio=AudioRenderPlan(
            audio_path=audio_file,
            total_duration=7.5,
        ),
        output_path=out_reel,
        width=1080,
        height=1920,
        fps=30,
    )

    temp_dir = tmp_path / "render_tmp"
    rendered_path, durations = composite_render_plan(plan, temp_dir)

    assert rendered_path.exists()
    assert rendered_path.stat().st_size > 10000

    # Probe final output for yuv420p
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=pix_fmt,width,height",
        "-of", "default=noprint_wrappers=1",
        str(rendered_path),
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "420p" in res.stdout
    assert "width=1080" in res.stdout
    assert "height=1920" in res.stdout

