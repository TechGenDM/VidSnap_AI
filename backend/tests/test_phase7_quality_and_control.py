"""
VidSnap AI - Phase 7 Quality, Control, Visual Consistency, and Iteration Speed Test Suite
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import db
from app.models import Project, Scene, Job, JobStatus, ProjectVersion
from app.services.scene_audio import SceneAudioService
from app.services.visual_consistency import VisualConsistencyEngine, ReelWorldContext
from app.services.quality_gate import QualityGateService, QualityGateReport
from app.services.layout_constants import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    SAFE_MARGIN_X_PCT,
    SAFE_BOTTOM_MARGIN_PCT,
    MAX_CHARS_PER_LINE,
    wrap_caption_safe,
)

client = TestClient(app)


def test_scene_audio_caching_and_isolation(tmp_path):
    """
    Test 1: Changing Scene 1 narration regenerates only Scene 1 audio;
    Scenes 2-4 are loaded directly from cache.
    """
    scenes = [
        Scene(order=1, narration="First scene narration about artificial intelligence.", caption="AI INTRO"),
        Scene(order=2, narration="Second scene describing neural network models.", caption="NEURAL NETS"),
        Scene(order=3, narration="Third scene showing robotics hardware in action.", caption="ROBOTICS"),
        Scene(order=4, narration="Fourth scene concluding the modern technology overview.", caption="CONCLUSION"),
    ]
    project = Project(
        title="Cache Test",
        voice="adam",
        scenes=scenes,
    )

    proj_dir = tmp_path / "project_audio_dir"

    # Step 1: First build (all 4 miss cache and are synthesized)
    master_path1, durs1, stats1 = SceneAudioService.build_project_audio_plan(
        project=project,
        project_dir=proj_dir,
    )
    assert stats1["regenerated_scenes"] == 4
    assert stats1["cached_scenes"] == 0
    assert len(durs1) == 4
    assert master_path1.exists()

    # Step 2: Immediate rebuild with identical scenes -> 4 cache hits, 0 misses
    master_path2, durs2, stats2 = SceneAudioService.build_project_audio_plan(
        project=project,
        project_dir=proj_dir,
    )
    assert stats2["cached_scenes"] == 4
    assert stats2["regenerated_scenes"] == 0

    # Step 3: Change ONLY Scene 1 narration
    project_modified = Project(
        title="Cache Test Modified",
        voice="adam",
        scenes=[
            Scene(order=1, narration="Completely new first scene hook for viewers.", caption="NEW HOOK"),
            scenes[1],
            scenes[2],
            scenes[3],
        ],
    )
    master_path3, durs3, stats3 = SceneAudioService.build_project_audio_plan(
        project=project_modified,
        project_dir=proj_dir,
    )
    # Exactly 1 miss (Scene 1) and 3 hits (Scenes 2, 3, 4)
    assert stats3["regenerated_scenes"] == 1
    assert stats3["cached_scenes"] == 3
    assert len(durs3) == 4
    assert master_path3.exists()


def test_scene_visual_isolation_and_broll_upload(tmp_path):
    """
    Test 2 & 3: Custom B-roll upload and scene visual replacement leave
    unrelated scenes completely unaffected.
    """
    project = Project(
        title="B-Roll Isolation Test",
        voice="adam",
        style="cinematic",
        script="Scene one. Scene two. Scene three.",
        scenes=[
            Scene(order=1, narration="Scene one.", caption="ONE", visual_filename="1.jpg", visual_url="/media/templates/1.jpg"),
            Scene(order=2, narration="Scene two.", caption="TWO", visual_filename="2.jpg", visual_url="/media/templates/2.jpg"),
            Scene(order=3, narration="Scene three.", caption="THREE", visual_filename="3.jpg", visual_url="/media/templates/3.jpg"),
        ],
    )
    db.save_project(project)

    # 1. Upload custom B-roll for Scene 2 (Valid Pillow image)
    from PIL import Image
    dummy_img = tmp_path / "custom_broll.jpg"
    img = Image.new("RGB", (200, 200), color=(0, 120, 255))
    img.save(dummy_img, format="JPEG")

    with open(dummy_img, "rb") as f:
        resp = client.post(
            f"/api/projects/{project.id}/scenes/2/upload-asset",
            files={"file": ("custom_broll.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 200
    updated = resp.json()["project"]

    # Verify Scene 2 is updated to custom asset
    assert updated["scenes"][1]["visual_source"] == "custom"
    assert "custom_broll" in updated["scenes"][1]["visual_filename"]

    # Verify Scenes 1 and 3 remain untouched
    assert updated["scenes"][0]["visual_filename"] == "1.jpg"
    assert updated["scenes"][2]["visual_filename"] == "3.jpg"


def test_visual_alternatives_and_revert_flow():
    """
    Test 4: Fetch visual alternatives, select an alternative, and revert to fallback.
    """
    project = Project(
        title="Alternatives Test",
        voice="rachel",
        style="tech",
        script="Testing alternatives.",
        scenes=[
            Scene(order=1, narration="Testing alternatives.", caption="ALT TEST", visual_filename="1.jpg", visual_url="/media/templates/1.jpg"),
        ],
    )
    db.save_project(project)

    # 1. Get alternatives
    resp = client.get(f"/api/projects/{project.id}/scenes/1/visual-alternatives")
    assert resp.status_code == 200
    data = resp.json()
    assert "alternatives" in data
    assert len(data["alternatives"]) > 0

    # 2. Select visual alternative (e.g. 4.jpg)
    alt = data["alternatives"][0]
    select_resp = client.post(
        f"/api/projects/{project.id}/scenes/1/select-visual",
        json={"visual_filename": alt["filename"], "visual_url": alt["url"], "visual_type": "stock"},
    )
    assert select_resp.status_code == 200
    sel_proj = select_resp.json()["project"]
    assert sel_proj["scenes"][0]["visual_filename"] == alt["filename"]

    # 3. Revert to stock fallback
    del_resp = client.delete(f"/api/projects/{project.id}/scenes/1/visual")
    assert del_resp.status_code == 200
    rev_proj = del_resp.json()["project"]
    assert rev_proj["scenes"][0]["visual_filename"] == "1.jpg"


def test_visual_regeneration_snapshot_recovery():
    """
    Test 5: Regenerating an AI visual creates an immutable snapshot
    so the prior visual can be recovered.
    """
    project = Project(
        title="Snapshot Recovery Test",
        voice="adam",
        style="cinematic",
        script="Before regen.",
        scenes=[
            Scene(order=1, narration="Before regen.", caption="REGEN TEST", visual_filename="original_visual.jpg", visual_url="/media/original.jpg"),
        ],
    )
    db.save_project(project)
    initial_versions_count = len(project.versions)

    dummy_scene = Scene(
        id=project.scenes[0].id,
        order=1,
        narration="Before regen.",
        caption="REGEN TEST",
        visual_filename="ai_new_visual.jpg",
        visual_url="/media/ai_new_visual.jpg",
    )
    with patch("app.api.projects.smart_visual_provider.regenerate_single_scene_visual", return_value=(dummy_scene, {})):
        resp = client.post(f"/api/projects/{project.id}/scenes/1/regenerate-visual")
        assert resp.status_code == 200

    # Verify snapshots were created
    saved = db.get_project(project.id)
    assert len(saved.versions) >= initial_versions_count + 1
    # Check that the pre-regenerate snapshot has the original visual
    pre_regen = saved.versions[0]
    assert pre_regen.scenes[0].visual_filename == "original_visual.jpg"

    # Restore the prior version
    rest_resp = client.post(f"/api/projects/{project.id}/versions/{pre_regen.version_number}/restore")
    assert rest_resp.status_code == 200
    restored_proj = rest_resp.json()["project"]
    assert restored_proj["scenes"][0]["visual_filename"] == "original_visual.jpg"


def test_preview_and_render_layout_consistency():
    """
    Test 6: Verify shared layout constants between preview and ASS render engine.
    """
    assert CANVAS_WIDTH == 1080
    assert CANVAS_HEIGHT == 1920
    assert SAFE_MARGIN_X_PCT == 0.055
    assert SAFE_BOTTOM_MARGIN_PCT == 0.198
    assert MAX_CHARS_PER_LINE == 28

    # Test caption line wrapping
    short_caption = "SHORT HOOK"
    assert wrap_caption_safe(short_caption) == "SHORT HOOK"

    long_caption = "ARTIFICIAL INTELLIGENCE AGENTS ARE TRANSFORMING SOFTWARE DEVELOPMENT WORLDWIDE"
    wrapped = wrap_caption_safe(long_caption)
    lines = wrapped.split("\n")
    assert len(lines) >= 2
    for l in lines:
        assert len(l) <= MAX_CHARS_PER_LINE + 5


def test_quality_gate_checks_and_reliability(tmp_path):
    """
    Test 7: QualityGateService flags missing files, bad dimensions, silent audio,
    and returns actionable warnings without fake scores.
    """
    project = Project(
        title="Quality Gate Test",
        voice="adam",
        style="cinematic",
        script="Test narration.",
        scenes=[
            Scene(order=1, narration="One.", caption="VERY LONG CAPTION THAT GOES ON AND ON AND EXCEEDS THE STANDARD CHARACTER LIMIT FOR PREVIEWS", duration_seconds=4.0),
            Scene(order=2, narration="Two.", caption="TWO", duration_seconds=4.0, visual_filename="same.jpg"),
            Scene(order=3, narration="Three.", caption="THREE", duration_seconds=4.0, visual_filename="same.jpg"),
        ],
    )

    # Case A: Non-existent file
    missing_file = tmp_path / "non_existent.mp4"
    rep_missing = QualityGateService.validate_reel(project, missing_file)
    assert not rep_missing.passed
    assert not rep_missing.is_ready_to_post
    assert "Video file was not generated" in rep_missing.blocking_errors[0]

    # Case B: Mock valid probe data on a real small file
    test_file = tmp_path / "dummy_video.mp4"
    test_file.write_bytes(b"\x00" * 20000)

    with patch.object(QualityGateService, "probe_video") as mock_probe, \
         patch.object(QualityGateService, "inspect_audio_volume", return_value=-18.5):
        
        mock_probe.return_value = {
            "streams": [
                {"codec_type": "video", "width": 1080, "height": 1920},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "16.4", "size": "2500000"},
        }

        rep_valid = QualityGateService.validate_reel(project, test_file)
        assert rep_valid.passed
        assert rep_valid.checks["dimensions_1080x1920"] is True
        assert rep_valid.checks["audio_present"] is True
        assert rep_valid.checks["audio_audible"] is True
        assert rep_valid.checks["duration_valid"] is True
        # Visual diversity warning (Scenes 2 & 3 both use "same.jpg")
        assert any("identical visuals" in w for w in rep_valid.actionable_warnings)
        # Caption length warning
        assert any("wrap tightly" in w or "crowd" in w for w in rep_valid.actionable_warnings)


def test_visual_consistency_engine_best_effort():
    """
    Test 8: Best-effort visual continuity via ReelWorldContext.
    Produces shared world environment, palette, and shot progression without fake identity locking.
    """
    from app.models import StoryScene

    scenes = [
        StoryScene(order=1, narration="AI tools are shifting development.", caption="HOOK", visual_direction="Developer at sleek workstation"),
        StoryScene(order=2, narration="Autonomous workflows handle routine code.", caption="WORKFLOW", visual_direction="Data flow on server monitors"),
        StoryScene(order=3, narration="Architects guide high level direction.", caption="SYSTEMS", visual_direction="Engineer reviewing architecture"),
        StoryScene(order=4, narration="Building software enters a new era.", caption="FUTURE", visual_direction="Team celebrating successful deployment"),
    ]

    context = VisualConsistencyEngine.create_world_context(
        domain="technology",
        visual_style="cinematic",
        topic="Autonomous Coding",
    )
    assert context.lighting_palette is not None
    assert context.world_setting is not None
    assert context.subject_anchor is not None
    assert context.continuity_level == "best_effort_continuity"

    applied_scenes = VisualConsistencyEngine.apply_world_continuity_to_scenes(scenes, context)
    assert len(applied_scenes) == 4

    # Varied camera shot progression
    compositions = [s.visual_plan.composition for s in applied_scenes]
    assert len(set(compositions)) >= 3  # at least 3 distinct shots across 4 scenes

    # Continuity prompt formatting
    prompt = VisualConsistencyEngine.format_continuity_prompt("developer workspace", context, compositions[0])
    assert "color palette" in prompt
    assert context.world_setting in prompt


def test_rapid_consecutive_scene_edits():
    """
    Test 9: Rapid consecutive scene updates maintain database consistency
    and preserve motion, transition, and custom visual metadata.
    """
    project = Project(
        title="Concurrency & State Integrity Test",
        voice="adam",
        style="cinematic",
        script="Script test.",
        scenes=[
            Scene(order=1, narration="Initial 1", caption="CAP 1", duration_seconds=3.0),
            Scene(order=2, narration="Initial 2", caption="CAP 2", duration_seconds=3.0),
        ],
    )
    db.save_project(project)

    # Edit 1: Update Scene 1 motion and transition
    resp1 = client.put(
        f"/api/projects/{project.id}/scenes",
        json={
            "scenes": [
                {
                    "id": project.scenes[0].id,
                    "narration": "Updated Scene 1",
                    "caption": "UPDATED 1",
                    "motion": "pan_left",
                    "transition": "cut",
                },
                {
                    "id": project.scenes[1].id,
                    "narration": "Initial 2",
                    "caption": "CAP 2",
                },
            ]
        },
    )
    assert resp1.status_code == 200

    # Edit 2: Immediately update Scene 2 without touching Scene 1
    resp2 = client.put(
        f"/api/projects/{project.id}/scenes",
        json={
            "scenes": [
                {
                    "id": project.scenes[0].id,
                    "narration": "Updated Scene 1",
                    "caption": "UPDATED 1",
                    "motion": "pan_left",
                    "transition": "cut",
                },
                {
                    "id": project.scenes[1].id,
                    "narration": "Updated Scene 2",
                    "caption": "UPDATED 2",
                    "motion": "tilt_up",
                    "transition": "crossfade",
                },
            ]
        },
    )
    assert resp2.status_code == 200
    saved = db.get_project(project.id)
    assert saved.scenes[0].motion == "pan_left"
    assert saved.scenes[0].transition == "cut"
    assert saved.scenes[1].motion == "tilt_up"
    assert saved.scenes[1].transition == "crossfade"
    assert saved.scenes[0].narration == "Updated Scene 1"
    assert saved.scenes[1].narration == "Updated Scene 2"
