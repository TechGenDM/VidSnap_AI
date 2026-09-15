"""
VidSnap AI - Quick Reel Narration & Full-Chain Audio Regression Test Suite

Verifies:
1. Creator script is correctly partitioned across scenes with zero word loss or corruption.
2. 'Scene preview' (or 'sin preview') is NEVER synthesized or passed to TTS.
3. Empty narration produces clean silence, never spoken placeholder text.
4. Different projects cannot reuse another project's narration/audio cache (cross-project isolation).
5. Editing scene narration rebuilds the audio cache and uses the updated text.
6. Full Pipeline Verification:
   creator script -> scene narration -> TTS input -> assembled audio -> final FFmpeg render -> final MP4
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.models import Project, Scene, CaptionSegment, CaptionWord
from app.services.jobs import derive_scene_caption, partition_script_across_scenes, process_quick_reel_job
from app.services.scene_audio import SceneAudioService
from app.services.storage import get_project_dir
from app.database import db

client = TestClient(app)


def test_script_partitioning_preserves_all_words():
    """
    Test 1: Script partitioning preserves every word without dropping or duplicating.
    """
    creator_script = (
        "Here is the secret to building high-performance web applications. "
        "First, optimize your database queries with proper indexing. "
        "Second, leverage edge caching for static and dynamic assets. "
        "Finally, monitor Core Web Vitals to keep user bounce rates under two percent."
    )
    scenes = [
        Scene(order=1, image_url="/tmp/dummy1.jpg"),
        Scene(order=2, image_url="/tmp/dummy2.jpg"),
        Scene(order=3, image_url="/tmp/dummy3.jpg"),
        Scene(order=4, image_url="/tmp/dummy4.jpg"),
    ]

    partition_script_across_scenes(creator_script, scenes)

    # All scenes must have narration and punchy uppercase captions
    for s in scenes:
        assert s.narration, f"Scene {s.order} narration must not be empty"
        assert s.caption, f"Scene {s.order} caption must not be empty"
        assert s.caption.isupper(), f"Scene {s.order} caption must be uppercase"
        assert "preview" not in s.narration.lower()
        assert "preview" not in s.caption.lower()

    # Reassembled narration must contain the original words
    combined_narration = " ".join([s.narration for s in scenes])
    original_words = creator_script.split()
    reconstructed_words = combined_narration.split()
    assert original_words == reconstructed_words, "All original words must be preserved in exact sequence"


def test_empty_narration_generates_silence_never_placeholder(tmp_path):
    """
    Test 2: Empty narration generates clean silence, NEVER synthesizes 'Scene preview' or any fallback phrase.
    """
    proj_dir = tmp_path / "test_empty_proj"
    proj_dir.mkdir(parents=True, exist_ok=True)

    empty_scene = Scene(order=1, narration="", caption="", duration_seconds=2.0)

    # Intercept TTS to ensure it is NEVER called for empty narration
    with patch("app.services.scene_audio.tts_service.generate_speech_with_alignment") as mock_tts:
        audio_path, duration, segments, align_src, was_cached = SceneAudioService.generate_or_reuse_scene_audio(
            project_dir=proj_dir,
            scene=empty_scene,
            voice="adam",
        )

        # TTS must not have been called!
        assert mock_tts.call_count == 0, "TTS service must NOT be called when narration is empty"
        assert align_src == "silence"
        assert len(segments) == 0
        assert audio_path.exists()
        assert audio_path.stat().st_size > 0

        # Check cached metadata
        meta_file = proj_dir / "audio_cache" / f"scene_{empty_scene.order}_{SceneAudioService.compute_scene_audio_hash(empty_scene.id, '__EMPTY_SILENCE__', 'adam', proj_dir.name)}.json"
        assert meta_file.exists()
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["narration"] == ""
        assert meta["alignment_source"] == "silence"
        assert "preview" not in json.dumps(meta).lower()


def test_cross_project_cache_isolation(tmp_path):
    """
    Test 3: Different projects cannot reuse another project's audio cache, even with identical scene order and text.
    """
    proj_a_dir = tmp_path / "project_alpha"
    proj_b_dir = tmp_path / "project_beta"
    proj_a_dir.mkdir(parents=True, exist_ok=True)
    proj_b_dir.mkdir(parents=True, exist_ok=True)

    text = "The quick brown fox jumps over the lazy dog."
    scene_id = "scene_001"

    hash_a = SceneAudioService.compute_scene_audio_hash(scene_id, text, "adam", project_id="project_alpha")
    hash_b = SceneAudioService.compute_scene_audio_hash(scene_id, text, "adam", project_id="project_beta")

    assert hash_a != hash_b, "Hash must incorporate project_id to prevent cross-project cache collisions"

    # Also verify directory isolation
    cache_a = SceneAudioService.get_cache_dir(proj_a_dir)
    cache_b = SceneAudioService.get_cache_dir(proj_b_dir)
    assert cache_a != cache_b
    assert cache_a.parent == proj_a_dir
    assert cache_b.parent == proj_b_dir


def test_editing_narration_invalidates_cache(tmp_path):
    """
    Test 4: Editing scene narration creates a new cache entry with updated text.
    """
    proj_dir = tmp_path / "project_edit"
    proj_dir.mkdir(parents=True, exist_ok=True)

    scene = Scene(order=1, narration="Initial draft narration.", caption="INITIAL", duration_seconds=2.0)

    # First synthesis
    p1, dur1, seg1, src1, cached1 = SceneAudioService.generate_or_reuse_scene_audio(
        project_dir=proj_dir,
        scene=scene,
        voice="adam",
    )
    assert p1.exists()
    assert cached1 is False

    # Second call with same text -> cache hit
    p2, dur2, seg2, src2, cached2 = SceneAudioService.generate_or_reuse_scene_audio(
        project_dir=proj_dir,
        scene=scene,
        voice="adam",
    )
    assert p2 == p1
    assert cached2 is True

    # Edit narration text
    scene.narration = "Updated draft narration with different vocabulary."
    p3, dur3, seg3, src3, cached3 = SceneAudioService.generate_or_reuse_scene_audio(
        project_dir=proj_dir,
        scene=scene,
        voice="adam",
    )
    assert p3 != p1, "Updated narration must produce a distinct audio file"
    assert cached3 is False, "Updated narration must be a cache MISS and regenerate"


def test_full_chain_quick_reel_render_artifact_verification(tmp_path):
    """
    Test 5: Full pipeline artifact verification:
    creator script -> scene narration -> TTS input -> assembled audio -> final FFmpeg render -> final MP4.

    Verifies:
    1. Every scene narration is derived from the creator script.
    2. Zero occurrences of 'Scene preview' sent to TTS or stored.
    3. Assembled raw voice track is generated.
    4. FFmpeg renders a valid MP4 with video & audio streams.
    5. Final video contains the audio track generated from the creator script.
    """
    creator_script = (
        "Building software with automated agents is transforming technology. "
        "Continuous feedback loops allow developers to ship reliable features faster."
    )

    # Create dummy images for 2 scenes
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.jpg"

    # Use ffmpeg to generate two 1080x1920 test images
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=1080x1920:d=1",
        "-frames:v", "1", str(img1)
    ], check=True, capture_output=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=purple:s=1080x1920:d=1",
        "-frames:v", "1", str(img2)
    ], check=True, capture_output=True)

    scenes = [
        Scene(order=1, image_url=str(img1), narration="", caption=""),
        Scene(order=2, image_url=str(img2), narration="", caption=""),
    ]

    project = Project(
        title="Quick Reel Full Chain Test",
        script=creator_script,
        voice="adam",
        scenes=scenes,
    )
    proj_dir = get_project_dir(project.id)
    proj_dir.mkdir(parents=True, exist_ok=True)
    db.save_project(project)

    try:
        tts_inputs_captured = []

        # Spy on TTS to inspect exact text received
        orig_generate_speech = SceneAudioService.generate_or_reuse_scene_audio

        def spy_generate_or_reuse(project_dir, scene, voice):
            tts_inputs_captured.append((scene.order, scene.narration))
            return orig_generate_speech(project_dir, scene, voice)

        with patch.object(SceneAudioService, "generate_or_reuse_scene_audio", side_effect=spy_generate_or_reuse):
            from app.models import Job
            job = Job(project_id=project.id)
            db.save_job(job)
            process_quick_reel_job(job.id)

        # 1. Inspect captured inputs
        assert len(tts_inputs_captured) == 2, "Both scenes must have been processed for audio"
        for order, narration in tts_inputs_captured:
            assert narration, f"Scene {order} narration must not be empty"
            assert "Scene preview" not in narration, f"Scene {order} narration must not be 'Scene preview'"
            assert "sin preview" not in narration.lower()
            assert "preview" not in narration.lower()

        # Combined narration must match the creator's original words
        all_captured_words = " ".join([t[1] for t in tts_inputs_captured]).split()
        assert all_captured_words == creator_script.split(), "Captured TTS narration words must equal creator script words"

        # 2. Inspect assembled audio file
        raw_voice_path = proj_dir / "voice_raw.mp3"
        assert raw_voice_path.exists(), "voice_raw.mp3 must be assembled"
        assert raw_voice_path.stat().st_size > 1000, "voice_raw.mp3 must contain audio data"

        # 3. Inspect final rendered MP4 artifact
        final_mp4 = settings.REELS_DIR / f"{project.id}.mp4"
        assert final_mp4.exists(), f"final_mp4 ({final_mp4}) must exist after render"
        assert final_mp4.stat().st_size > 10000, "final MP4 must not be empty"

        # Inspect stream metadata via ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,codec_name,width,height,duration",
            "-of", "json",
            str(final_mp4),
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(probe_res.stdout)
        streams = probe_data.get("streams", [])

        video_stream = next((s for s in streams if s["codec_type"] == "video"), None)
        audio_stream = next((s for s in streams if s["codec_type"] == "audio"), None)

        assert video_stream is not None, "Final MP4 must have a video stream"
        assert video_stream["width"] == 1080
        assert video_stream["height"] == 1920

        assert audio_stream is not None, "Final MP4 must have an audio stream"
        final_audio_duration = float(audio_stream.get("duration", 0) or probe_data.get("format", {}).get("duration", 0))
        assert final_audio_duration > 1.0, f"Final audio duration ({final_audio_duration}s) must be > 1.0s"

        # 4. Verify project state in database
        saved_proj = db.get_project(project.id)
        assert saved_proj is not None
        assert saved_proj.status.value in ["completed", "ready"]
        for s in saved_proj.scenes:
            assert s.narration, f"Scene {s.order} must have saved narration"
            assert "preview" not in s.narration.lower()
            assert len(s.caption_segments) > 0, f"Scene {s.order} must have word-level aligned caption segments"
            # Verify words in captions correspond to narration
            seg_words = [w.text for seg in s.caption_segments for w in seg.words]
            for w in s.narration.split():
                clean_w = w.strip(".,!?:;\"'").lower()
                assert any(clean_w == sw.strip(".,!?:;\"'").lower() for sw in seg_words), f"Word '{w}' from narration must appear in aligned caption words"

    finally:
        # Cleanup
        import shutil
        if proj_dir.exists():
            shutil.rmtree(proj_dir, ignore_errors=True)
        rendered_video = settings.REELS_DIR / f"{project.id}.mp4"
        if rendered_video.exists():
            rendered_video.unlink(missing_ok=True)
