"""
VidSnap AI - Phase 3 Visual Intelligence & Cinematic Rendering Tests
Validates:
1. VisualPlanningEngine (domain, role, tone, and visual plan generation)
2. AssetCatalog (metadata, semantic scoring, diversity, anti-consecutive duplicate rule, match quality)
3. MotionEngine (all 6 motion presets, portrait-safe expressions, filter validity)
4. TitleQualityValidator (awkward title rejection, natural title formatting)
5. RenderPlan & RenderPlanBuilder (validation, scene item construction, audio plan)
6. Frame Inspection heuristics (1080x1920, 9:16, border checks, contrast)
"""

import pytest
from pathlib import Path
from PIL import Image
from app.models import StoryScene, Project, VisualPlan, CaptionSegment
from app.services.visual_planning import VisualPlanningEngine
from app.services.asset_catalog import AssetCatalog, default_asset_catalog, AssetMetadata
from app.services.motion import MotionEngine
from app.services.creative_engine import TitleQualityValidator
from app.services.render_plan import RenderPlan, RenderPlanBuilder, SceneRenderItem, AudioRenderPlan
from app.services.video import inspect_rendered_frames, render_scene_segment
from app.config import settings


# ---------------------------------------------------------------------------
# 1. Visual Planning Engine Tests
# ---------------------------------------------------------------------------

def test_visual_planning_engine_scene_roles():
    """Verifies that scene roles dictate cinematic motion and transitions."""
    hook_scene = StoryScene(
        order=1,
        narration="AI agents are fundamentally changing who writes code.",
        caption="NOT JUST AUTOCOMPLETE",
        visual_direction="Developer looking at an intelligent agent workflow",
        estimated_duration=4.0,
        scene_role="hook",
    )
    plan = VisualPlanningEngine.plan_scene_visuals(
        scene=hook_scene,
        domain="technology",
        tone="Energetic",
        visual_style="Minimal Tech",
    )
    assert plan.motion == "slow_zoom_in"
    assert plan.transition in ["cut", "short_fade"]
    assert plan.composition == "medium_close_up"
    assert plan.visual_type in ["developer_workstation", "global_network", "architecture_flowchart"]

    example_scene = StoryScene(
        order=3,
        narration="For example, agents refactor architecture while developers steer intent.",
        caption="STEER INTENT",
        visual_direction="System topology diagram",
        estimated_duration=5.0,
        scene_role="example",
    )
    plan_ex = VisualPlanningEngine.plan_scene_visuals(
        scene=example_scene,
        domain="technology",
        tone="Educational",
        visual_style="Minimal Tech",
    )
    assert plan_ex.motion == "pan_right"
    assert plan_ex.transition == "directional_slide"
    assert plan_ex.composition == "overhead_desk"


def test_visual_planning_five_domains():
    """Ensures each domain generates specialized visual plans."""
    domains = ["technology", "science", "education", "business", "personal"]
    for d in domains:
        scene = StoryScene(
            order=1,
            narration=f"Exploring key concepts in {d}.",
            caption="KEY CONCEPTS",
            visual_direction=f"Contextual representation of {d}",
            estimated_duration=4.0,
            scene_role="insight",
        )
        plan = VisualPlanningEngine.plan_scene_visuals(scene=scene, domain=d)
        assert plan.visual_type
        assert plan.subject
        assert plan.environment
        assert plan.mood
        assert plan.motion in MotionEngine.SUPPORTED_MOTIONS


# ---------------------------------------------------------------------------
# 2. Asset Catalog & Selection Intelligence Tests
# ---------------------------------------------------------------------------

def test_asset_catalog_metadata_integrity():
    """Verifies all catalog template assets have complete, structured metadata."""
    assets = default_asset_catalog.get_all_assets()
    assert len(assets) == 5
    for a in assets:
        assert a.id.startswith("template_")
        assert a.filename.endswith(".jpg")
        assert len(a.tags) >= 5
        assert len(a.moods) >= 2
        assert len(a.subjects) >= 1
        assert len(a.visual_types) >= 1
        assert a.composition


def test_anti_consecutive_duplicate_and_diversity_rules():
    """Verifies the catalog will never select consecutive duplicates and penalizes recent reuse."""
    catalog = default_asset_catalog
    plan = VisualPlan(
        scene_id=1,
        visual_type="developer_workstation",
        subject="developer",
        environment="dark minimalist workspace",
        composition="medium_close_up",
        mood="focused",
        motion="slow_zoom_in",
        transition="cut",
        emphasis="code editor",
    )

    # First scene selection
    first_asset, match_1 = catalog.select_best_asset(
        visual_plan=plan,
        scene_text="developer typing code in terminal",
        domain="technology",
        visual_style="Minimal Tech",
        previously_used=[],
    )
    assert first_asset.filename == "1.jpg"

    # Second scene has identical requirements, but MUST NOT repeat consecutive asset
    second_asset, match_2 = catalog.select_best_asset(
        visual_plan=plan,
        scene_text="developer typing code in terminal",
        domain="technology",
        visual_style="Minimal Tech",
        previously_used=[first_asset.filename],
    )
    assert second_asset.filename != first_asset.filename, "Consecutive scenes must not duplicate assets"


def test_honest_match_quality_classification():
    """Verifies exact matches vs approximate matches are accurately labeled without false AI claims."""
    catalog = default_asset_catalog
    tech_plan = VisualPlan(
        scene_id=1,
        visual_type="developer_workstation",
        subject="developer",
        environment="dark studio",
        composition="medium_close_up",
        mood="focused",
        motion="slow_zoom_in",
        transition="cut",
        emphasis="code",
    )
    _, match_quality_tech = catalog.select_best_asset(
        visual_plan=tech_plan,
        scene_text="developer typing syntax in code editor",
        domain="technology",
        visual_style="Minimal Tech",
        previously_used=[],
    )
    assert match_quality_tech == "exact"

    # Plan with unfamiliar/unmatched concept should yield approximate
    unmatched_plan = VisualPlan(
        scene_id=2,
        visual_type="underwater_coral_reef",
        subject="marine_turtle",
        environment="deep pacific ocean",
        composition="underwater_macro",
        mood="submerged",
        motion="slow_zoom_out",
        transition="crossfade",
        emphasis="coral",
    )
    _, match_quality_unmatched = catalog.select_best_asset(
        visual_plan=unmatched_plan,
        scene_text="underwater submarine exploration",
        domain="science",
        visual_style="Cinematic",
        previously_used=[],
    )
    assert match_quality_unmatched == "approximate"


# ---------------------------------------------------------------------------
# 3. Motion Engine Tests
# ---------------------------------------------------------------------------

def test_motion_engine_presets():
    """Verifies all 6 motion presets generate valid, non-empty, portrait-safe filter expressions."""
    for motion in MotionEngine.SUPPORTED_MOTIONS:
        flt = MotionEngine.build_motion_filter(motion=motion, duration=3.0, fps=30)
        assert "scale=1620:2880" in flt
        assert "crop=1620:2880" in flt
        assert "s=1080x1920" in flt
        assert "fps=30" in flt
        assert "setsar=1" in flt


# ---------------------------------------------------------------------------
# 4. Title Quality Validator Tests
# ---------------------------------------------------------------------------

def test_title_quality_validator_clean_and_validate():
    """Verifies awkward formulations are rejected and natural titles are formatted."""
    # Test awkward title detection
    bad_titles = [
        "The Truth About Why Is The Sky Blue",
        "The Truth About How The Internet Works",
        "You Won't Believe What Happens",
        "Shocking Secrets of AI",
    ]
    for bt in bad_titles:
        is_val, errs = TitleQualityValidator.validate_title(bt)
        assert not is_val, f"Expected '{bt}' to be rejected"
        assert len(errs) > 0

    # Test clean title generation
    t1 = TitleQualityValidator.clean_title(prompt="Why is the sky blue?", topic="the sky")
    assert t1 == "Why Is the Sky Blue?"

    t2 = TitleQualityValidator.clean_title(
        prompt="Explain why AI agents are changing software development.",
        topic="AI agents",
    )
    assert t2 == "Why AI Agents Are Changing Software Development?"

    t3 = TitleQualityValidator.clean_title(
        prompt="What I learned from building my first AI project",
        topic="my first AI project",
    )
    assert t3 == "What I Learned from Building My First AI Project"


# ---------------------------------------------------------------------------
# 5. Render Plan & Builder Tests
# ---------------------------------------------------------------------------

def test_render_plan_validation(tmp_path):
    """Verifies RenderPlan fails cleanly if required assets or audio are missing."""
    dummy_img = tmp_path / "test.jpg"
    img = Image.new("RGB", (1080, 1920), color=(30, 30, 40))
    img.save(dummy_img, "JPEG")

    dummy_audio = tmp_path / "audio.aac"
    dummy_audio.write_bytes(b"dummy_audio_data")

    # Valid plan
    valid_scene = SceneRenderItem(
        scene_id="s1",
        order=1,
        image_path=dummy_img,
        duration=3.0,
        caption="TEST CAPTION",
        motion="slow_zoom_in",
        transition="cut",
    )
    plan = RenderPlan(
        project_id="p1",
        scenes=[valid_scene],
        audio=AudioRenderPlan(audio_path=dummy_audio, total_duration=3.0),
        output_path=tmp_path / "out.mp4",
    )
    assert len(plan.validate()) == 0

    # Missing image
    invalid_scene = SceneRenderItem(
        scene_id="s2",
        order=2,
        image_path=tmp_path / "non_existent.jpg",
        duration=3.0,
        caption="TEST",
        motion="slow_zoom_in",
        transition="cut",
    )
    bad_plan = RenderPlan(
        project_id="p1",
        scenes=[invalid_scene],
        audio=AudioRenderPlan(audio_path=dummy_audio, total_duration=3.0),
        output_path=tmp_path / "out.mp4",
    )
    errors = bad_plan.validate()
    assert len(errors) > 0
    assert any("does not exist" in e for e in errors)


# ---------------------------------------------------------------------------
# 6. Frame Inspection Tests
# ---------------------------------------------------------------------------

def test_inspect_rendered_frames_on_test_video():
    """Verifies that inspect_rendered_frames correctly checks resolution, aspect ratio, and metrics."""
    test_video = Path("/Users/devasishmishra/Developer/TechGenDM_Codes/Coding Web Playground /VidSnap_AI/scratch_test/presets/slow_zoom_in.mp4")
    if not test_video.exists():
        pytest.skip("Test video not available in scratch directory")

    inspect_dir = test_video.parent / "test_inspection"
    res = inspect_rendered_frames(test_video, inspect_dir)
    assert res.resolution == (1080, 1920)
    assert res.aspect_ratio == "9:16"
    assert not res.has_black_borders
    assert not res.is_corrupted
    assert res.passed
    assert len(res.frame_paths) == 3
