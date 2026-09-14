import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import db
from app.models import LifecycleState, Project

client = TestClient(app)

def test_creator_presets_endpoint():
    """Validates that GET /api/assets/presets and /api/presets return 5 fully configured creator presets."""
    res = client.get("/api/assets/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) == 5

    preset_ids = [p["id"] for p in presets]
    assert "tech_creator" in preset_ids
    assert "educational" in preset_ids
    assert "storytelling" in preset_ids
    assert "product_showcase" in preset_ids
    assert "personal_story" in preset_ids

    # Verify each preset defines mandatory configuration defaults
    for p in presets:
        assert p["tone"]
        assert p["visual_style"]
        assert p["caption_style"]
        assert p["voice"]
        assert p["music"]
        assert p["length"]

    # Also test top-level /api/presets
    res_top = client.get("/api/presets")
    assert res_top.status_code == 200
    assert len(res_top.json()) == 5

def test_version_history_true_snapshot_and_immutability():
    """
    Mandatory Requirement 1:
    1. Project is created and modified multiple times.
    2. An older version is restored.
    3. The restored project matches that historical state.
    4. Later modifications do not alter the historical snapshot.
    5. Version records are immutable and restore creates a new current state with clear labels.
    """
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain why AI agents are changing software development.",
        "audience": "Tech Creators",
        "tone": "Educational",
        "length": "30s",
        "visual_style": "Minimal Tech",
        "voice": "adam",
    })
    assert create_res.status_code == 200
    project_id = create_res.json()["project_id"]
    
    # Check initial snapshot (v1)
    v_res = client.get(f"/api/projects/{project_id}/versions")
    assert v_res.status_code == 200
    v_list = v_res.json()
    assert len(v_list) >= 1
    v1 = v_list[0]
    assert v1["version_number"] == 1
    v1_hook = v1["hook"]
    v1_voice = v1["voice"]

    # Modification 1: Assistant command "Make the hook stronger"
    res_mod1 = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Make the hook stronger"
    })
    assert res_mod1.status_code == 200
    mod1_hook = res_mod1.json()["project"]["scenes"][0]["narration"]
    assert mod1_hook != v1_hook

    # Modification 2: Change voice and energy
    res_mod2 = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Make the tone more energetic"
    })
    assert res_mod2.status_code == 200
    assert res_mod2.json()["project"]["voice"] == "josh"

    # Modification 3: Make shorter
    res_mod3 = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Make this shorter"
    })
    assert res_mod3.status_code == 200

    # Inspect version history
    v_res2 = client.get(f"/api/projects/{project_id}/versions")
    v_list2 = v_res2.json()
    assert len(v_list2) >= 4  # v1 + 3 pre-change snapshots

    # Historical snapshot v1 must remain untouched!
    snapshot_v1 = next(v for v in v_list2 if v["version_number"] == 1)
    assert snapshot_v1["hook"] == v1_hook
    assert snapshot_v1["voice"] == v1_voice

    # Restore Version 1
    restore_res = client.post(f"/api/projects/{project_id}/versions/1/restore")
    assert restore_res.status_code == 200
    restored_proj = restore_res.json()["project"]
    
    # Verify current state matches Version 1
    assert restored_proj["scenes"][0]["narration"] == v1_hook
    assert restored_proj["voice"] == v1_voice

    # Perform another modification after restore
    res_after = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Make this more provocative"
    })
    assert res_after.status_code == 200

    # Ensure historical Version 1 snapshot was NEVER modified by later actions
    v_res3 = client.get(f"/api/projects/{project_id}/versions")
    v_list3 = v_res3.json()
    snapshot_v1_final = next(v for v in v_list3 if v["version_number"] == 1)
    assert snapshot_v1_final["hook"] == v1_hook
    assert snapshot_v1_final["voice"] == v1_voice

def test_deterministic_and_explainable_ask_vidsnap():
    """
    Mandatory Requirement 2:
    Tests all supported deterministic intents and unsupported commands.
    """
    create_res = client.post("/api/reels/ai", json={
        "prompt": "How quantum computing solves optimization problems.",
        "audience": "Tech Creators",
        "tone": "Educational",
        "length": "30s",
        "visual_style": "cinematic",
        "voice": "adam",
    })
    assert create_res.status_code == 200
    project_id = create_res.json()["project_id"]

    supported_commands = [
        "Make the hook stronger",
        "Make this more provocative",
        "Make this 20 seconds",
        "Make this shorter",
        "Make this more technical",
        "Make it sound more conversational",
        "Use simpler language",
        "Replace scene 2",
        "Change the visual for scene 1",
        "Give me a stronger ending",
        "Remove unnecessary repetition",
    ]

    for cmd in supported_commands:
        res = client.post(f"/api/projects/{project_id}/assistant", json={"command": cmd})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["action"]) > 5
        assert "project" in data
        assert len(data["project"]["scenes"]) >= 1

    # Verify Unsupported Command
    unsupported_res = client.post(f"/api/projects/{project_id}/assistant", json={
        "command": "Do a backflip and generate music video in 4K"
    })
    assert unsupported_res.status_code == 200
    unsupp_data = unsupported_res.json()
    assert unsupp_data["success"] is False
    assert "couldn't recognize" in unsupp_data["action"].lower() or "not supported" in unsupp_data["action"].lower()
    assert "Supported creator commands" in unsupp_data["action"]

def test_try_another_hook_flow():
    """
    Mandatory Requirement 3:
    1. Hook alternatives produce real variations in angle/strategy.
    2. Applying alternative updates Scene 1 narration & caption and canonical story while preserving remaining scenes.
    """
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Explain the Pareto principle in daily productivity.",
        "audience": "General Audience",
        "tone": "Educational",
        "length": "30s",
    })
    project_id = create_res.json()["project_id"]
    orig_scenes = create_res.json()["scenes"]

    # Fetch alternative hooks
    alt_res = client.get(f"/api/projects/{project_id}/alternatives/hook")
    assert alt_res.status_code == 200
    alt_data = alt_res.json()
    assert alt_data["status"] == "success"
    alternatives = alt_data["alternatives"]
    assert len(alternatives) == 2
    assert alternatives[0]["hook"] != alternatives[1]["hook"]
    assert alternatives[0]["strategy"] != alternatives[1]["strategy"]

    # Select alternative 1 and apply
    chosen = alternatives[0]
    apply_res = client.post(f"/api/projects/{project_id}/apply-hook", json={
        "hook": chosen["hook"],
        "caption": chosen["caption"],
    })
    assert apply_res.status_code == 200
    applied_proj = apply_res.json()["project"]

    # Scene 1 must have the chosen hook and caption
    assert applied_proj["scenes"][0]["narration"] == chosen["hook"]
    assert applied_proj["scenes"][0]["caption"] == chosen["caption"]

    # Remaining scenes must be preserved
    assert len(applied_proj["scenes"]) == len(orig_scenes)
    for idx in range(1, len(applied_proj["scenes"])):
        assert applied_proj["scenes"][idx]["id"] == orig_scenes[idx]["id"]

def test_project_duplication_independence():
    """
    Mandatory Requirement 10:
    Duplicating a project must produce an independent project:
    - new project ID
    - independent story/scenes
    - independent version history
    - no accidental shared mutable state
    """
    create_res = client.post("/api/reels/ai", json={
        "prompt": "How SpaceX reuses rocket boosters.",
        "voice": "adam",
    })
    orig_proj = create_res.json()
    orig_id = orig_proj["project_id"]

    # Duplicate project
    dup_res = client.post(f"/api/projects/{orig_id}/duplicate")
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    dup_id = dup_data["id"]

    assert dup_id != orig_id
    assert "(Variant)" in dup_data["title"]
    assert len(dup_data["scenes"]) == len(orig_proj["scenes"])

    # Modify duplicate
    client.post(f"/api/projects/{dup_id}/assistant", json={
        "command": "Make this more provocative"
    })
    client.put(f"/api/projects/{dup_id}/scenes", json={
        "scenes": [{"id": dup_data["scenes"][0]["id"], "narration": "MODIFIED DUPLICATE HOOK"}]
    })

    # Ensure original project was NOT affected
    orig_check = client.get(f"/api/projects/{orig_id}").json()
    assert orig_check["scenes"][0]["narration"] != "MODIFIED DUPLICATE HOOK"

    # Version history must be independent
    orig_versions = client.get(f"/api/projects/{orig_id}/versions").json()
    dup_versions = client.get(f"/api/projects/{dup_id}/versions").json()
    assert orig_versions[0]["title"] != dup_versions[0]["title"] or orig_versions != dup_versions

def test_qualitative_feedback_honesty():
    """
    Mandatory Requirement 9:
    Qualitative feedback must be explainable bullets derived from concrete story characteristics,
    avoiding arbitrary numeric quality scores.
    """
    create_res = client.post("/api/reels/ai", json={
        "prompt": "Why deep work produces outsized creative results.",
    })
    data = create_res.json()
    feedback = data["qualitative_feedback"]

    assert isinstance(feedback, list)
    assert len(feedback) >= 2
    # Ensure all feedback items are qualitative strings
    for item in feedback:
        assert isinstance(item, str)
        assert len(item) > 10
        # No arbitrary "Quality: 92/100"
        assert "/100" not in item
        assert "score:" not in item.lower()

def test_creation_metrics_telemetry():
    """
    Mandatory Requirement 5 & 6:
    Creation metrics track genuine generation timing and lifecycle state transitions.
    """
    create_res = client.post("/api/reels/ai", json={
        "prompt": "How distributed databases handle eventual consistency.",
    })
    data = create_res.json()
    assert data["lifecycle_state"] == LifecycleState.STORY_READY

    metrics = data["metrics"]
    assert metrics["story_generation_ms"] is not None
    assert metrics["story_generation_ms"] > 0
    assert metrics["time_to_first_story_ms"] is not None
    assert metrics["time_to_first_preview_ms"] is not None
