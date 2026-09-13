import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Story, StoryScene
from app.services.story_generation import LocalStoryProvider, get_story_provider
from app.services.visual_provider import LocalAssetProvider
from app.database import db

client = TestClient(app)

def test_valid_structured_story_generation():
    """Verify that LocalStoryProvider outputs strict, valid Pydantic Story objects."""
    provider = LocalStoryProvider()
    story = provider.generate_story(
        prompt="Explain why AI agents are changing software development.",
        audience="Tech Creators",
        tone="Educational",
        length="30s",
        style="Minimal Tech",
        variation_seed=0,
    )

    assert isinstance(story, Story)
    assert len(story.title) > 3
    assert len(story.hook) > 5
    assert len(story.scenes) >= 3
    assert len(story.cta) > 3
    assert story.estimated_duration > 0

    for scene in story.scenes:
        assert isinstance(scene, StoryScene)
        assert scene.order > 0
        assert len(scene.narration) > 5
        assert len(scene.caption) > 0
        assert len(scene.visual_direction) > 5
        assert scene.estimated_duration > 0

def test_malformed_story_pydantic_rejection():
    """Verify that Story model rejects malformed or missing fields."""
    with pytest.raises(Exception):
        Story.model_validate({
            "title": "Short",
            # missing hook
            "scenes": [],
            "cta": "Click",
        })

    with pytest.raises(Exception):
        StoryScene.model_validate({
            "order": 1,
            "narration": "", # Empty narration not allowed
            "caption": "Cap",
            "visual_direction": "Visual",
        })

def test_story_regeneration_variation():
    """Verify that regenerating a story with variation seeds creates distinct hooks & angles."""
    provider = LocalStoryProvider()
    prompt = "Explain why AI agents are changing software development."

    story_v0 = provider.generate_story(prompt=prompt, variation_seed=0)
    story_v1 = provider.generate_story(prompt=prompt, variation_seed=1)
    story_v2 = provider.generate_story(prompt=prompt, variation_seed=2)

    # Hooks must be meaningfully different
    assert story_v0.hook != story_v1.hook
    assert story_v1.hook != story_v2.hook
    assert story_v0.scenes[0].caption != story_v1.scenes[0].caption

def test_single_scene_regeneration():
    """Verify that a single scene can be regenerated independently."""
    provider = LocalStoryProvider()
    story = provider.generate_story(prompt="Explain AI coding tools", length="30s")

    original_scene_2 = story.scenes[1]
    new_scene_2 = provider.regenerate_scene(story=story, scene_order=2, prompt="Explain AI coding tools")

    assert new_scene_2.order == 2
    assert new_scene_2.narration != original_scene_2.narration
    assert new_scene_2.caption != original_scene_2.caption

def test_local_visual_matching():
    """Verify LocalAssetProvider matches existing templates and creates self-contained copies."""
    import uuid
    provider = LocalAssetProvider()
    scenes = [
        StoryScene(order=1, narration="Intro", caption="Intro", visual_direction="Developer coding", estimated_duration=4.0),
        StoryScene(order=2, narration="Body", caption="Body", visual_direction="Architecture map", estimated_duration=4.0),
    ]

    test_proj_id = str(uuid.uuid4())
    matched_scenes = provider.match_visuals_for_scenes(
        scenes=scenes,
        visual_style="Minimal Tech",
        project_id=test_proj_id,
    )

    assert len(matched_scenes) == 2
    assert matched_scenes[0].visual_filename == "scene_1.jpg"
    assert matched_scenes[1].visual_filename == "scene_2.jpg"
    assert f"/media/uploads/{test_proj_id}/" in matched_scenes[0].visual_url

def test_ai_reel_project_creation_and_prompt_persistence():
    """Verify POST /api/reels/ai generates planned story and preserves original prompt."""
    payload = {
        "prompt": "Explain why AI agents are changing software development.",
        "audience": "Tech Creators",
        "tone": "Educational",
        "length": "30s",
        "visual_style": "Minimal Tech",
        "voice": "adam",
        "music": "ambient_chill",
    }

    res = client.post("/api/reels/ai", json=payload)
    assert res.status_code == 200
    data = res.json()

    project_id = data["project_id"]
    assert data["status"] == "planned"
    assert "story" in data
    assert len(data["scenes"]) >= 3

    # Verify project persistence in db
    project = db.get_project(project_id)
    assert project is not None
    assert project.source_type == "ai"
    assert project.mode == "ai"
    assert project.original_prompt == payload["prompt"]
    assert project.audience == "Tech Creators"
    assert project.tone == "Educational"
    assert project.target_length == "30s"
    assert project.generated_story is not None
    assert project.generated_story.title == data["story"]["title"]

def test_api_story_regeneration():
    """Verify POST /api/projects/{id}/regenerate-story regenerates with new angle."""
    # First create project
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain why AI agents are changing software development.",
        "audience": "Tech Creators",
        "tone": "Educational",
        "length": "30s",
        "visual_style": "Minimal Tech",
    })
    project_id = create_res.json()["project_id"]
    initial_hook = create_res.json()["story"]["hook"]

    # Trigger story regeneration
    regen_res = client.post(f"/api/projects/{project_id}/regenerate-story")
    assert regen_res.status_code == 200
    regen_data = regen_res.json()

    assert regen_data["status"] == "success"
    assert regen_data["story"]["hook"] != initial_hook

    # Check project in DB has updated render history
    proj = db.get_project(project_id)
    assert len(proj.render_history) >= 1
    assert proj.render_history[0]["action"] == "regenerate_story"

def test_api_single_scene_regeneration():
    """Verify POST /api/projects/{id}/scenes/{order}/regenerate updates one scene."""
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain why AI agents are changing software development.",
    })
    project_id = create_res.json()["project_id"]
    orig_scene_1 = create_res.json()["scenes"][0]

    regen_res = client.post(f"/api/projects/{project_id}/scenes/1/regenerate", json={
        "feedback": "Make it punchier"
    })
    assert regen_res.status_code == 200
    updated_scene = regen_res.json()["scene"]

    assert updated_scene["order"] == 1
    assert updated_scene["narration"] != orig_scene_1["narration"]

def test_api_scene_deletion():
    """Verify DELETE /api/projects/{id}/scenes/{order} deletes and re-indexes scenes."""
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain why AI agents are changing software development.",
    })
    project_id = create_res.json()["project_id"]
    initial_scene_count = len(create_res.json()["scenes"])

    del_res = client.delete(f"/api/projects/{project_id}/scenes/2")
    assert del_res.status_code == 200

    proj = db.get_project(project_id)
    assert len(proj.scenes) == initial_scene_count - 1
    # Check 1-based order continuity
    for idx, s in enumerate(proj.scenes):
        assert s.order == idx + 1

def test_ask_vidsnap_actions():
    """Verify Ask VidSnap assistant commands update canonical scene model."""
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain why AI agents are changing software development.",
    })
    project_id = create_res.json()["project_id"]

    # 1. Attention-grabbing intro
    res_hook = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Make the intro more attention-grabbing"
    })
    assert res_hook.status_code == 200
    proj = db.get_project(project_id)
    assert "STOP SCROLLING" in proj.scenes[0].caption

    # 2. Make shorter
    orig_count = len(proj.scenes)
    res_short = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Make this shorter"
    })
    assert res_short.status_code == 200
    proj = db.get_project(project_id)
    assert len(proj.scenes) == orig_count - 1

    # 3. Change voice
    res_voice = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Change the voice to Rachel"
    })
    assert res_voice.status_code == 200
    proj = db.get_project(project_id)
    assert proj.voice == "rachel"

def test_ai_reel_to_render_pipeline():
    """Verify end-to-end flow: AI Reel story generation -> POST render -> finished MP4 Reel."""
    # Step 1: Generate AI Reel story
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain why AI agents are changing software development.",
        "audience": "Tech Creators",
        "tone": "Educational",
        "length": "15s", # Quick 3-scene reel for test speed
        "visual_style": "Minimal Tech",
        "voice": "adam",
        "music": "ambient_chill",
    })
    assert create_res.status_code == 200
    project_id = create_res.json()["project_id"]

    # Step 2: Trigger render using existing pipeline
    render_res = client.post(f"/api/projects/{project_id}/render")
    assert render_res.status_code == 200
    job_id = render_res.json()["job_id"]

    # Step 3: Wait for job completion
    import time
    max_wait = 30
    completed = False
    for _ in range(max_wait):
        job_res = client.get(f"/api/jobs/{job_id}")
        assert job_res.status_code == 200
        job_data = job_res.json()
        if job_data["status"] == "completed":
            completed = True
            break
        elif job_data["status"] == "failed":
            pytest.fail(f"Render job failed: {job_data.get('error_message')}")
        time.sleep(1)

    assert completed, "AI Reel render job did not complete within timeout"

    # Step 4: Verify completed project
    proj_res = client.get(f"/api/projects/{project_id}")
    assert proj_res.status_code == 200
    proj_data = proj_res.json()
    assert proj_data["status"] == "completed"
    assert proj_data["video_url"] is not None
    assert proj_data["thumbnail_url"] is not None
    assert proj_data["duration_seconds"] > 0
    assert len(proj_data["render_history"]) >= 1
