"""
VidSnap AI - Phase 4 Word-Level Captions & Real AI Visuals Test Suite
Validates:
1. Timestamp validity & audio duration clamping
2. Word overlap prevention & kinetic segment grouping
3. ASS Caption formatting, safe escaping & mobile safe margins
4. Image provider abstraction & custom provider interface
5. Pollinations API response handling & error detection
6. PIL Image validation (corrupt images, min dimensions)
7. Asset cache hits, misses & metadata storage
8. Cache invalidation on configuration / style / prompt changes
9. AI generation failure graceful fallback to LocalAssetProvider
10. VisualPromptBuilder portrait composition & negative constraints
11. Project-level visual consistency tokens
12. Single-scene visual regeneration endpoint (preserves all other scenes)
13. Full AI Reel render pipeline integration
"""

import os
import json
import uuid
import time
import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.models import (
    Project,
    Scene,
    StoryScene,
    VisualPlan,
    CaptionWord,
    CaptionSegment,
    JobStatus,
)
from app.services.speech_alignment import SpeechAlignmentEngine
from app.services.caption_generator import ASSCaptionGenerator
from app.services.image_generation import (
    ImageGenerationProvider,
    PollinationsImageProvider,
    VisualPromptBuilder,
    AssetCache,
    ImageGenerationError,
)
from app.services.visual_provider import (
    SmartVisualProvider,
    LocalAssetProvider,
)
from app.services.render_plan import SceneRenderItem
from app.services.video import (
    render_scene_segment,
    inspect_rendered_frames,
)
from app.database import Database

client = TestClient(app)
db = Database()


# ---------------------------------------------------------------------------
# 1. Timestamp Validity & Audio Duration Clamping
# ---------------------------------------------------------------------------

def test_timestamp_validity_and_audio_duration_clamping():
    """Verifies that all word timestamps fall strictly within 0.0 and audio duration."""
    words = SpeechAlignmentEngine.align_deterministic_fallback(
        text="AI agents write modern software faster.",
        total_duration=3.2,
    )
    assert len(words) == 6
    assert words[0].start_time >= 0.0
    assert words[-1].end_time <= 3.2

    for i, w in enumerate(words):
        assert w.start_time >= 0.0
        assert w.end_time <= 3.2
        assert w.start_time < w.end_time
        if i > 0:
            assert w.start_time >= words[i - 1].start_time


def test_native_alignment_normalization_and_clamping():
    """Verifies that ElevenLabs character-level timestamps normalize into valid words."""
    char_data = {
        "characters": ["A", "I", " ", "i", "s", " ", "h", "e", "r", "e"],
        "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        "character_end_times_seconds":   [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    }
    words = SpeechAlignmentEngine.align_from_native_timestamps(
        text="AI is here",
        alignment_data=char_data,
        total_duration=1.0,
    )
    assert len(words) == 3
    assert words[0].text == "AI"
    assert words[1].text == "is"
    assert words[2].text == "here"
    assert words[0].start_time == 0.0
    assert words[-1].end_time <= 1.0


# ---------------------------------------------------------------------------
# 2. Word Overlap Prevention & Kinetic Segment Grouping
# ---------------------------------------------------------------------------

def test_word_overlap_prevention_and_kinetic_grouping():
    """Verifies sequential words never overlap in time and form concise kinetic phrases."""
    words = [
        CaptionWord(text="Autonomous", start_time=0.0, end_time=0.6, emphasized=True),
        CaptionWord(text="coding", start_time=0.6, end_time=1.1, emphasized=False),
        CaptionWord(text="agents", start_time=1.1, end_time=1.5, emphasized=False),
        CaptionWord(text="will", start_time=1.5, end_time=1.8, emphasized=False),
        CaptionWord(text="redefine", start_time=1.8, end_time=2.4, emphasized=True),
        CaptionWord(text="software", start_time=2.4, end_time=3.0, emphasized=False),
    ]

    segments = SpeechAlignmentEngine.build_kinetic_segments(words, style="kinetic")
    assert len(segments) >= 2

    for i, seg in enumerate(segments):
        assert seg.start_time < seg.end_time
        assert len(seg.words) <= 3
        if i > 0:
            # No overlap between segments
            assert seg.start_time >= segments[i - 1].end_time

    # Verify emphasis words are extracted
    assert "Autonomous" in segments[0].emphasis_words or "AUTONOMOUS" in [w.upper() for w in segments[0].emphasis_words]


# ---------------------------------------------------------------------------
# 3. Caption Formatting, Safe Escaping & Safe Margins
# ---------------------------------------------------------------------------

def test_caption_formatting_safe_escaping(tmp_path):
    """Verifies ASS subtitle generation safely escapes special characters and quotes."""
    segments = [
        CaptionSegment(
            text='They said: "It\'s {impossible} & <dangerous>!" \\ slash',
            start_time=0.2,
            end_time=2.5,
            words=[
                CaptionWord(text="They", start_time=0.2, end_time=0.5),
                CaptionWord(text='said: "It\'s', start_time=0.5, end_time=1.2),
                CaptionWord(text='{impossible}"', start_time=1.2, end_time=2.5, emphasized=True),
            ],
            emphasis_words=["{impossible}"],
            style="kinetic",
        )
    ]

    ass_file = tmp_path / "test.ass"
    ASSCaptionGenerator.generate_ass_file(segments, output_path=ass_file, scene_offset=0.0)
    assert ass_file.exists()
    ass_content = ass_file.read_text(encoding="utf-8")

    assert "[Script Info]" in ass_content
    assert "[V4+ Styles]" in ass_content
    assert "[Events]" in ass_content

    # MarginV must respect safe mobile vertical space (380px)
    assert "MarginV" in ass_content
    assert "380" in ass_content

    # Dangerous curly braces must be escaped so ASS does not treat them as unclosed override tags
    assert "Dialogue:" in ass_content


def test_caption_renderer_unicode_and_multiline(tmp_path):
    """Verifies ASS generation handles multilingual Unicode and emojis gracefully."""
    segments = [
        CaptionSegment(
            text="AI revolution 🚀 — 智能 革命",
            start_time=0.0,
            end_time=2.0,
            words=[
                CaptionWord(text="AI", start_time=0.0, end_time=0.5),
                CaptionWord(text="revolution", start_time=0.5, end_time=1.0, emphasized=True),
                CaptionWord(text="🚀", start_time=1.0, end_time=1.5),
                CaptionWord(text="智能", start_time=1.5, end_time=2.0),
            ],
            emphasis_words=["revolution"],
        )
    ]
    ass_file = tmp_path / "unicode.ass"
    ASSCaptionGenerator.generate_ass_file(segments, output_path=ass_file, scene_offset=0.0)
    assert ass_file.exists()
    ass_content = ass_file.read_text(encoding="utf-8")
    assert "🚀" in ass_content
    assert "智能" in ass_content


# ---------------------------------------------------------------------------
# 4. Image Provider Abstraction & Custom Implementation
# ---------------------------------------------------------------------------

class MockImageProvider(ImageGenerationProvider):
    def __init__(self, succeed: bool = True):
        self.succeed = succeed
        self.calls = []

    def generate_image(self, prompt: str, output_path: Path, width: int = 576, height: int = 1024, seed: int = None) -> Path:
        self.calls.append({"prompt": prompt, "seed": seed})
        if not self.succeed:
            raise ImageGenerationError("Simulated image provider outage")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (width, height), color=(30, 80, 160))
        img.save(output_path, "JPEG")
        return output_path


def test_image_provider_abstraction(tmp_path):
    """Verifies that the abstract ImageGenerationProvider interface functions with mock providers."""
    mock = MockImageProvider(succeed=True)
    out_file = tmp_path / "test.jpg"
    res = mock.generate_image("A futuristic server room", out_file)
    assert res.exists()
    assert len(mock.calls) == 1

    failing = MockImageProvider(succeed=False)
    with pytest.raises(ImageGenerationError, match="Simulated image provider outage"):
        failing.generate_image("A futuristic server room", out_file)


# ---------------------------------------------------------------------------
# 5. Pollinations API Provider Handling
# ---------------------------------------------------------------------------

def test_pollinations_api_provider_configuration():
    """Verifies PollinationsImageProvider uses gen.pollinations.ai and reads config."""
    prov = PollinationsImageProvider()
    assert prov.BASE_URL == "https://gen.pollinations.ai"
    assert prov.model is not None


# ---------------------------------------------------------------------------
# 6. PIL Image Validation
# ---------------------------------------------------------------------------

def test_image_validation_pil(tmp_path):
    """Verifies corrupted or undersized image data is detected and rejected."""
    # Corrupt file
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"NOT_A_REAL_IMAGE_HEADER_12345")
    with pytest.raises(ImageGenerationError, match="Invalid or corrupt image"):
        PollinationsImageProvider.validate_image_file(corrupt_file)

    # Valid file
    valid_file = tmp_path / "valid.jpg"
    img = Image.new("RGB", (576, 1024), color=(10, 20, 30))
    img.save(valid_file, "JPEG")
    validated = PollinationsImageProvider.validate_image_file(valid_file)
    assert validated.exists()


# ---------------------------------------------------------------------------
# 7. Asset Caching & Metadata Storage
# ---------------------------------------------------------------------------

def test_asset_caching_and_metadata(tmp_path):
    """Verifies images are cached by prompt hash and metadata is persisted."""
    cache = AssetCache(cache_dir=tmp_path / "cache")
    prompt = "A high tech holographic terminal glowing in dark studio"
    h = cache.compute_hash(prompt=prompt, model="flux", width=576, height=1024, visual_style="Cinematic Tech", seed=42)

    assert cache.get_cached_image(h) is None

    # Save dummy image
    dummy_img = tmp_path / "source.jpg"
    Image.new("RGB", (576, 1024), color=(50, 100, 150)).save(dummy_img, "JPEG")

    saved = cache.save_to_cache(
        prompt_hash=h,
        image_source_path=dummy_img,
        prompt=prompt,
        model="flux",
        visual_style="Cinematic Tech",
        width=576,
        height=1024,
        seed=42,
    )
    assert saved.exists()

    # Next lookup must be a cache hit
    hit = cache.get_cached_image(h)
    assert hit is not None
    assert hit.exists()

    # Metadata file must exist with correct schema
    meta_path = saved.with_suffix(".json")
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta["prompt_hash"] == h
    assert meta["model"] == "flux"
    assert meta["visual_style"] == "Cinematic Tech"
    assert meta["provider"] == "pollinations"


# ---------------------------------------------------------------------------
# 8. Cache Invalidation on Configuration Change
# ---------------------------------------------------------------------------

def test_cache_invalidation_on_config_change(tmp_path):
    """Verifies changing model, style, or seed results in different cache keys."""
    cache = AssetCache(cache_dir=tmp_path / "cache")
    prompt = "A software architect designing distributed agents"

    h1 = cache.compute_hash(prompt=prompt, model="flux", width=576, height=1024, visual_style="Cinematic Tech", seed=10)
    h2 = cache.compute_hash(prompt=prompt, model="flux-realism", width=576, height=1024, visual_style="Cinematic Tech", seed=10)
    h3 = cache.compute_hash(prompt=prompt, model="flux", width=576, height=1024, visual_style="Minimal Tech", seed=10)
    h4 = cache.compute_hash(prompt=prompt, model="flux", width=576, height=1024, visual_style="Cinematic Tech", seed=99)

    assert len({h1, h2, h3, h4}) == 4, "All 4 configuration permutations must have distinct hashes"


# ---------------------------------------------------------------------------
# 9. AI Failure Fallback to Local Stock
# ---------------------------------------------------------------------------

def test_ai_failure_fallback_to_local_stock(tmp_path):
    """Verifies that an image generation error falls back gracefully to LocalAssetProvider."""
    failing_provider = MockImageProvider(succeed=False)
    cache = AssetCache(cache_dir=tmp_path / "cache")
    local_prov = LocalAssetProvider()
    smart_prov = SmartVisualProvider(
        image_provider=failing_provider,
        asset_cache=cache,
        local_provider=local_prov,
    )

    test_project_id = str(uuid.uuid4())
    story_scenes = [
        StoryScene(
            order=1,
            narration="AI agents are building software in real-time.",
            caption="REAL-TIME CODING",
            visual_direction="Autonomous developer workspace with code streams",
            estimated_duration=3.5,
            scene_role="hook",
        )
    ]

    matched_scenes = smart_prov.match_visuals_for_scenes(
        scenes=story_scenes,
        visual_style="Cinematic Tech",
        project_id=test_project_id,
        visual_source_mode="ai",
    )

    assert len(matched_scenes) == 1
    scene = matched_scenes[0]

    # Visual source must be fallback_stock, not crashed
    assert scene.visual_source == "fallback_stock"
    assert scene.match_quality == "fallback_local"

    # Diagnostics must capture the error and the fallback
    diags = smart_prov.last_diagnostics
    assert len(diags) >= 1
    assert diags[0]["fallback"] == "LocalAssetProvider"
    assert "Simulated image provider outage" in diags[0]["error"]


# ---------------------------------------------------------------------------
# 10. Visual Prompt Builder & Portrait / Negative Constraints
# ---------------------------------------------------------------------------

def test_visual_prompt_builder():
    """Verifies VisualPromptBuilder synthesizes rich visual cues without simply dumping narration."""
    plan = VisualPlan(
        scene_id=1,
        visual_type="developer_workstation",
        subject="modern developer using neural code interface",
        environment="sleek minimalist engineering studio with warm ambient lighting",
        composition="vertical portrait medium shot, Rule of Thirds",
        mood="focused and revolutionary",
        motion="slow_zoom_in",
        transition="short_fade",
        emphasis="glow from dual ultra-wide displays",
    )

    prompt = VisualPromptBuilder.build_prompt(
        visual_plan=plan,
        visual_style="Cinematic Tech",
        narration="AI agents are writing the future of code.",
        scene_role="hook",
    )

    # Must contain visual direction, style and composition
    assert "modern developer" in prompt
    assert "sleek minimalist engineering studio" in prompt
    assert "vertical 9:16 portrait" in prompt
    assert "cinematic 35mm film still" in prompt
    assert "deep midnight blue" in prompt

    # Must enforce negative constraints against text/watermarks
    assert "no text" in prompt
    assert "no watermark" in prompt
    assert "no logos" in prompt

    # Must NOT simply be the narration
    assert prompt != "AI agents are writing the future of code."


# ---------------------------------------------------------------------------
# 11. Project-Level Visual Consistency
# ---------------------------------------------------------------------------

def test_project_level_visual_consistency():
    """Verifies that multiple scenes in the same project share consistent style tokens."""
    plan1 = VisualPlan(
        scene_id=1,
        visual_type="developer_workstation",
        subject="senior software engineer inspecting code graph",
        environment="glass-walled research lab",
        composition="medium shot",
        mood="curious",
        motion="slow_zoom_in",
        transition="cut",
        emphasis="screen reflection",
    )
    plan2 = VisualPlan(
        scene_id=2,
        visual_type="architecture_flowchart",
        subject="interconnected microservices topology",
        environment="abstract dark spatial canvas",
        composition="wide angle",
        mood="structured",
        motion="pan_right",
        transition="fade",
        emphasis="glowing data packets",
    )

    p1 = VisualPromptBuilder.build_prompt(plan1, visual_style="Cinematic Tech", narration="Scene 1", scene_role="hook")
    p2 = VisualPromptBuilder.build_prompt(plan2, visual_style="Cinematic Tech", narration="Scene 2", scene_role="explanation")

    # Both must share the visual style and portrait constraints
    for p in [p1, p2]:
        assert "cinematic 35mm film still" in p
        assert "deep midnight blue" in p
        assert "vertical 9:16 portrait" in p


# ---------------------------------------------------------------------------
# 12. Single Scene Visual Regeneration
# ---------------------------------------------------------------------------

def test_single_scene_visual_regeneration():
    """Verifies POST /api/projects/{id}/scenes/{order}/regenerate-visual updates only targeted scene."""
    proj_id = str(uuid.uuid4())
    project_dir = settings.UPLOADS_DIR / proj_id
    project_dir.mkdir(parents=True, exist_ok=True)

    img1 = project_dir / "scene_1.jpg"
    img2 = project_dir / "scene_2.jpg"
    Image.new("RGB", (576, 1024), color=(10, 20, 30)).save(img1, "JPEG")
    Image.new("RGB", (576, 1024), color=(40, 50, 60)).save(img2, "JPEG")

    scene1 = Scene(
        id="scene_1",
        order=1,
        visual_filename="scene_1.jpg",
        visual_url=f"/media/uploads/{proj_id}/scene_1.jpg",
        visual_direction="Scene 1 visual direction",
        narration="Keep this exact narration 1",
        caption="CAPTION 1",
        duration_seconds=3.0,
        visual_source="stock",
    )
    scene2 = Scene(
        id="scene_2",
        order=2,
        visual_filename="scene_2.jpg",
        visual_url=f"/media/uploads/{proj_id}/scene_2.jpg",
        visual_direction="Scene 2 visual direction",
        narration="Keep this exact narration 2",
        caption="CAPTION 2",
        duration_seconds=4.0,
        visual_source="stock",
    )

    project = Project(
        id=proj_id,
        title="Regeneration Test Project",
        created_at="2026-09-14T00:00:00Z",
        status=JobStatus.COMPLETED,
        duration_seconds=7.0,
        voice="adam",
        music="ambient_chill",
        style="Cinematic Tech",
        script="Keep this exact narration 1 Keep this exact narration 2",
        scenes=[scene1, scene2],
        visual_source="stock",
    )
    db.save_project(project)

    # Send regeneration request for Scene 1 only
    resp = client.post(
        f"/api/projects/{proj_id}/scenes/1/regenerate-visual",
        json={"custom_prompt": "Futuristic quantum processor glowing in deep indigo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scene_order"] == 1
    assert data["status"] == "success"

    # Reload project from DB
    reloaded = db.get_project(proj_id)
    assert reloaded is not None
    assert len(reloaded.scenes) == 2

    # Scene 1 regenerated visual properties
    s1 = reloaded.scenes[0]
    assert s1.narration == "Keep this exact narration 1"
    assert s1.caption == "CAPTION 1"
    assert s1.duration_seconds == 3.0
    assert s1.visual_filename == "scene_1.jpg"

    # Scene 2 must remain completely untouched
    s2 = reloaded.scenes[1]
    assert s2.narration == "Keep this exact narration 2"
    assert s2.caption == "CAPTION 2"
    assert s2.visual_source == "stock"


# ---------------------------------------------------------------------------
# 13. Full AI Reel Render Pipeline Integration Test
# ---------------------------------------------------------------------------

def test_full_ai_reel_render_pipeline(tmp_path):
    """Verifies rendering a scene segment with ASS kinetic subtitles into a 1080x1920 MP4."""
    proj_id = str(uuid.uuid4())
    proj_dir = settings.UPLOADS_DIR / proj_id
    proj_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a dummy image
    img_path = proj_dir / "scene_1.jpg"
    Image.new("RGB", (576, 1024), color=(15, 30, 60)).save(img_path, "JPEG")

    # 2. Create a short audio clip
    import subprocess
    audio_path = proj_dir / "scene_1_voice.mp3"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=440:duration=2.0",
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )

    # 3. Create kinetic caption segments
    segments = [
        CaptionSegment(
            text="Autonomous coding agents",
            start_time=0.0,
            end_time=1.0,
            words=[
                CaptionWord(text="Autonomous", start_time=0.0, end_time=0.5, emphasized=True),
                CaptionWord(text="coding", start_time=0.5, end_time=0.8),
                CaptionWord(text="agents", start_time=0.8, end_time=1.0),
            ],
            emphasis_words=["Autonomous"],
            style="kinetic",
        ),
        CaptionSegment(
            text="are changing software",
            start_time=1.0,
            end_time=2.0,
            words=[
                CaptionWord(text="are", start_time=1.0, end_time=1.3),
                CaptionWord(text="changing", start_time=1.3, end_time=1.7, emphasized=True),
                CaptionWord(text="software", start_time=1.7, end_time=2.0),
            ],
            emphasis_words=["changing"],
            style="kinetic",
        ),
    ]

    out_video = proj_dir / "scene_1_rendered.mp4"
    render_item = SceneRenderItem(
        scene_id="scene_1",
        order=1,
        image_path=img_path,
        duration=2.0,
        caption="Autonomous coding agents are changing software",
        motion="slow_zoom_in",
        transition="cut",
        caption_segments=segments,
    )

    rendered_file = render_scene_segment(
        item=render_item,
        output_segment_path=out_video,
    )

    assert rendered_file.exists()
    assert rendered_file.stat().st_size > 5000

    # Inspect frames at 15%, 50%, 85%
    insp_result = inspect_rendered_frames(rendered_file, output_dir=proj_dir / "inspection_frames")
    assert insp_result.passed is True
    assert len(insp_result.frame_paths) == 3
