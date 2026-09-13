"""
Phase 2.5 - Creative Intelligence & Output Quality Tests.
Validates:
- Rejection of known low-quality regression examples (generic openings, filler, tautologies)
- Strict caption constraints (2-7 words, no narration mirroring)
- Multi-domain storytelling across Technology, Science, Education, Business, and Personal categories
- Meaningful angle variation across seeds
- Context-aware scene regeneration preserving scene roles
- Visual provider diversity (anti-consecutive-duplicate rule) and match quality
- Story-aware Ask VidSnap assistant adjustments
- Acceptance quality standard for AI agent software development story
"""

import pytest
from app.models import Story, StoryScene
from app.services.creative_engine import (
    TopicInterpreter,
    StoryQualityValidator,
    StoryEvaluator,
    generate_high_quality_story,
)
from app.services.story_generation import LocalStoryProvider
from app.services.visual_provider import LocalAssetProvider
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_regression_bad_outputs_rejected():
    """
    Ensures that known low-quality patterns are rejected by StoryQualityValidator:
    - 'Today we are going to talk about AI agents.'
    - 'AI agents are changing software development because AI agents are changing software development.'
    - 'This topic is very interesting and important.'
    - 'Let’s dive into this amazing topic.'
    """
    prompt = "Explain why AI agents are changing software development."

    # 1. Generic opening: Today we are going to talk about...
    bad_hook_story = Story(
        title="AI Agents",
        hook="Today we are going to talk about AI agents.",
        scenes=[
            StoryScene(order=1, narration="Today we are going to talk about AI agents.", caption="AI AGENTS INTRO", visual_direction="Developer at desk", estimated_duration=7.0),
            StoryScene(order=2, narration="They are very useful tools.", caption="USEFUL TOOLS", visual_direction="Code on screen", estimated_duration=7.0),
            StoryScene(order=3, narration="They help write functions.", caption="WRITING FUNCTIONS", visual_direction="Dark room", estimated_duration=7.0),
            StoryScene(order=4, narration="Let us see what happens next.", caption="SEE WHAT HAPPENS", visual_direction="Terminal window", estimated_duration=7.0),
        ],
        cta="Follow for more.",
        estimated_duration=28.0,
    )
    is_valid, errors = StoryQualityValidator.validate_candidate(bad_hook_story, prompt)
    assert not is_valid
    assert any("Generic hook detected" in e for e in errors)

    # 2. Tautological repetition: X because X
    tautology_story = Story(
        title="AI Agents",
        hook="A quiet shift is happening in software.",
        scenes=[
            StoryScene(order=1, narration="A quiet shift is happening in software.", caption="QUIET SHIFT", visual_direction="Developer at desk", estimated_duration=7.0),
            StoryScene(order=2, narration="AI agents are changing software development because AI agents are changing software development.", caption="REDUNDANT CLAIM", visual_direction="Code on screen", estimated_duration=7.0),
            StoryScene(order=3, narration="They help write functions.", caption="WRITING FUNCTIONS", visual_direction="Dark room", estimated_duration=7.0),
            StoryScene(order=4, narration="Let us see what happens next.", caption="SEE WHAT HAPPENS", visual_direction="Terminal window", estimated_duration=7.0),
        ],
        cta="Follow for more.",
        estimated_duration=28.0,
    )
    is_valid, errors = StoryQualityValidator.validate_candidate(tautology_story, prompt)
    assert not is_valid
    assert any("Tautological repetition detected" in e for e in errors)

    # 3. Obvious filler: This topic is very interesting and important
    filler_story = Story(
        title="AI Agents",
        hook="The future of software is evolving.",
        scenes=[
            StoryScene(order=1, narration="The future of software is evolving.", caption="FUTURE EVOLVING", visual_direction="Developer at desk", estimated_duration=7.0),
            StoryScene(order=2, narration="This topic is very interesting and important for everyone building apps.", caption="INTERESTING TOPIC", visual_direction="Code on screen", estimated_duration=7.0),
            StoryScene(order=3, narration="Without further ado, let us inspect the architecture.", caption="NO DELAY", visual_direction="Dark room", estimated_duration=7.0),
            StoryScene(order=4, narration="Let us see what happens next.", caption="SEE WHAT HAPPENS", visual_direction="Terminal window", estimated_duration=7.0),
        ],
        cta="Follow for more.",
        estimated_duration=28.0,
    )
    is_valid, errors = StoryQualityValidator.validate_candidate(filler_story, prompt)
    assert not is_valid
    assert any("Obvious filler detected" in e for e in errors)

    # 4. Generic opening: Let's dive into this amazing topic
    dive_story = Story(
        title="AI Agents",
        hook="Let's dive into this amazing topic together.",
        scenes=[
            StoryScene(order=1, narration="Let's dive into this amazing topic together.", caption="DIVE IN", visual_direction="Developer at desk", estimated_duration=7.0),
            StoryScene(order=2, narration="Software is built by developers every day.", caption="SOFTWARE BUILT", visual_direction="Code on screen", estimated_duration=7.0),
            StoryScene(order=3, narration="Agents will help speed it up.", caption="SPEED UP", visual_direction="Dark room", estimated_duration=7.0),
            StoryScene(order=4, narration="Let us see what happens next.", caption="SEE WHAT HAPPENS", visual_direction="Terminal window", estimated_duration=7.0),
        ],
        cta="Follow for more.",
        estimated_duration=28.0,
    )
    is_valid, errors = StoryQualityValidator.validate_candidate(dive_story, prompt)
    assert not is_valid
    assert any("Generic hook detected" in e or "Obvious filler detected" in e for e in errors)

def test_caption_length_and_duplication_rules():
    """Validates that captions are strictly 2-7 words and not identical to narration."""
    prompt = "Explain why AI agents are changing software development."

    # Too short (< 2 words)
    too_short = Story(
        title="AI Agents",
        hook="A quiet shift is happening in software.",
        scenes=[
            StoryScene(order=1, narration="A quiet shift is happening in software.", caption="Code", visual_direction="Developer at desk", estimated_duration=7.0),
            StoryScene(order=2, narration="Developers now direct systems.", caption="DIRECT SYSTEMS", visual_direction="Code on screen", estimated_duration=7.0),
            StoryScene(order=3, narration="They verify outcomes.", caption="VERIFY OUTCOMES", visual_direction="Dark room", estimated_duration=7.0),
            StoryScene(order=4, narration="That is the shift.", caption="THE SHIFT", visual_direction="Terminal window", estimated_duration=7.0),
        ],
        cta="Follow for more.",
        estimated_duration=28.0,
    )
    is_valid, errors = StoryQualityValidator.validate_candidate(too_short, prompt)
    assert not is_valid
    assert any("caption is too short" in e for e in errors)

    # Too long (> 7 words)
    too_long = Story(
        title="AI Agents",
        hook="A quiet shift is happening in software.",
        scenes=[
            StoryScene(order=1, narration="A quiet shift is happening in software.", caption="AI agents are changing software development because they allow developers to build fast", visual_direction="Developer at desk", estimated_duration=7.0),
            StoryScene(order=2, narration="Developers now direct systems.", caption="DIRECT SYSTEMS", visual_direction="Code on screen", estimated_duration=7.0),
            StoryScene(order=3, narration="They verify outcomes.", caption="VERIFY OUTCOMES", visual_direction="Dark room", estimated_duration=7.0),
            StoryScene(order=4, narration="That is the shift.", caption="THE SHIFT", visual_direction="Terminal window", estimated_duration=7.0),
        ],
        cta="Follow for more.",
        estimated_duration=28.0,
    )
    is_valid, errors = StoryQualityValidator.validate_candidate(too_long, prompt)
    assert not is_valid
    assert any("caption is too long" in e for e in errors)

def test_five_domain_categories():
    """
    Tests creative generation across all 5 required product categories:
    1. Technology: Explain why AI agents are changing software development.
    2. Science: Why is the sky blue?
    3. Education: How does the internet actually work?
    4. Business: Why do startups struggle to find product-market fit?
    5. Personal: What I learned from building my first AI project.
    """
    test_cases = [
        ("Explain why AI agents are changing software development.", "technology"),
        ("Why is the sky blue?", "science"),
        ("How does the internet actually work?", "education"),
        ("Why do startups struggle to find product-market fit?", "business"),
        ("What I learned from building my first AI project.", "personal"),
    ]

    provider = LocalStoryProvider()

    for prompt, expected_domain in test_cases:
        interp = TopicInterpreter.interpret(prompt)
        assert interp.domain == expected_domain, f"Failed domain classification for: '{prompt}'"
        assert len(interp.hook_angles) >= 4
        assert interp.core_claim
        assert interp.audience_value
        assert interp.interesting_tension

        story = provider.generate_story(prompt=prompt, length="30s")
        assert isinstance(story, Story)
        assert len(story.scenes) == 4
        assert story.quality_score is not None
        assert story.quality_score >= 0.70

        # Validate captions are strictly 2-7 words
        for s in story.scenes:
            words = s.caption.split()
            assert 2 <= len(words) <= 7, f"Invalid caption length '{s.caption}' for '{prompt}'"
            assert s.scene_role in ["hook", "context", "insight", "example", "implication", "cta"]
            # No generic filler
            assert "today we are going to" not in s.narration.lower()
            assert "very interesting and important" not in s.narration.lower()

def test_variation_seeds_produce_distinct_angles():
    """Verifies that variation seeds switch hook strategies and creative angles."""
    provider = LocalStoryProvider()
    prompt = "Explain why AI agents are changing software development."

    s0 = provider.generate_story(prompt=prompt, variation_seed=0)
    s1 = provider.generate_story(prompt=prompt, variation_seed=1)
    s2 = provider.generate_story(prompt=prompt, variation_seed=2)

    # Hooks must be distinct
    assert s0.hook != s1.hook
    assert s1.hook != s2.hook
    assert s0.hook_strategy != s1.hook_strategy or s1.hook_strategy != s2.hook_strategy

def test_context_aware_scene_regeneration():
    """Regenerating a scene must preserve the scene's narrative role and domain context."""
    provider = LocalStoryProvider()
    prompt = "Why is the sky blue?"
    story = provider.generate_story(prompt=prompt, length="30s")

    scene_2 = story.scenes[1]
    assert scene_2.scene_role == "context"

    new_scene_2 = provider.regenerate_scene(story=story, scene_order=2, prompt=prompt)
    assert new_scene_2.order == 2
    assert new_scene_2.scene_role == "context"
    assert new_scene_2.narration != scene_2.narration
    assert 2 <= len(new_scene_2.caption.split()) <= 7

def test_visual_provider_anti_duplication_and_match_quality():
    """Verifies that LocalAssetProvider avoids consecutive duplicate templates and assigns match quality."""
    import uuid
    provider = LocalAssetProvider()
    scenes = [
        StoryScene(order=1, narration="Intro", caption="INTRO", visual_direction="Developer writing code at a dark IDE", estimated_duration=4.0, scene_role="hook"),
        StoryScene(order=2, narration="Next", caption="NEXT", visual_direction="Developer typing in an editor again", estimated_duration=4.0, scene_role="insight"),
        StoryScene(order=3, narration="Third", caption="THIRD", visual_direction="Interconnected cloud network architecture", estimated_duration=4.0, scene_role="implication"),
    ]

    matched = provider.match_visuals_for_scenes(scenes=scenes, visual_style="Minimal Tech", project_id=str(uuid.uuid4()))
    assert len(matched) == 3

    # Consecutive scenes must not use the exact same template filename
    assert matched[0].visual_filename != matched[1].visual_filename or len(provider._get_available_templates()) <= 1
    assert matched[1].visual_filename != matched[2].visual_filename or len(provider._get_available_templates()) <= 1

    # Check match quality
    for m in matched:
        assert m.match_quality in ["exact", "approximate"]
        assert m.scene_role in ["hook", "insight", "implication"]

def test_story_aware_assistant_actions():
    """Tests story-aware assistant commands on an existing project."""
    # Create project through API
    create_res = client.post(
        "/api/reels/ai",
        json={
            "prompt": "Explain why AI agents are changing software development.",
            "audience": "Tech Creators",
            "tone": "Educational",
            "length": "30s",
            "visual_style": "Minimal Tech",
            "voice": "adam",
        },
    )
    assert create_res.status_code == 200
    data = create_res.json()
    project_id = data["project_id"]

    # 1. Attention-grabbing intro
    hook_res = client.post(
        f"/api/projects/{project_id}/assistant",
        json={"command": "Make the intro more attention-grabbing"},
    )
    assert hook_res.status_code == 200
    updated_proj = hook_res.json()["project"]
    assert "bottleneck" in updated_proj["scenes"][0]["narration"].lower() or "friction" in updated_proj["scenes"][0]["narration"].lower()
    assert 2 <= len(updated_proj["scenes"][0]["caption"].split()) <= 7

    # 2. Make this more technical
    tech_res = client.post(
        f"/api/projects/{project_id}/assistant",
        json={"command": "Make this more technical"},
    )
    assert tech_res.status_code == 200
    tech_proj = tech_res.json()["project"]
    assert any("ast" in s["narration"].lower() or "orchestration" in s["narration"].lower() for s in tech_proj["scenes"])

    # 3. Make this shorter
    short_res = client.post(
        f"/api/projects/{project_id}/assistant",
        json={"command": "Make this shorter"},
    )
    assert short_res.status_code == 200
    short_proj = short_res.json()["project"]
    assert short_proj["duration_seconds"] < updated_proj["duration_seconds"]

    # 4. Make the tone more energetic
    energetic_res = client.post(
        f"/api/projects/{project_id}/assistant",
        json={"command": "Make the tone more energetic"},
    )
    assert energetic_res.status_code == 200
    energetic_proj = energetic_res.json()["project"]
    assert energetic_proj["voice"] == "josh"
    assert energetic_proj["music"] == "upbeat_pulse"

def test_acceptance_story_quality_standard():
    """
    Acceptance Test for the standard set in User Requirement #18:
    For: 'Explain why AI agents are changing software development.'
    The story should demonstrate high-retention human conversational writing:
    - Clear distinction between writing syntax vs directing outcomes
    - No generic openings or robotic tautologies
    - Kinetic screen captions (2-7 words)
    - Natural, engaging CTA
    """
    provider = LocalStoryProvider()
    story = provider.generate_story(
        prompt="Explain why AI agents are changing software development.",
        audience="Tech Creators",
        tone="Educational",
        length="30s",
        style="Minimal Tech",
        variation_seed=0,
    )

    assert "today we" not in story.hook.lower()
    assert "explain why" not in story.hook.lower()
    assert len(story.hook.split()) >= 8

    full_narration = " ".join([s.narration for s in story.scenes])
    assert "syntax" in full_narration.lower() or "orchestration" in full_narration.lower() or "writing" in full_narration.lower()
    assert "level" in full_narration.lower() or "autonomous" in full_narration.lower()

    for s in story.scenes:
        assert 2 <= len(s.caption.split()) <= 7
        assert s.scene_role in ["hook", "context", "insight", "implication", "cta"]
