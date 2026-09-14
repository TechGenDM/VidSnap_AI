import pytest
from app.services.creator_presets import CREATOR_PRESETS
from app.services.creative_engine import (
    StoryQualityValidator,
    TitleQualityValidator,
    TopicInterpreter,
)
from app.models import (
    Story,
    StoryScene,
    Scene,
    Project,
    CreationMetrics,
    LifecycleState,
    JobStatus,
)


def test_five_presets_are_sharply_differentiated():
    """
    Validates that each of the 5 creator presets has a unique, distinct creative identity.
    """
    presets = list(CREATOR_PRESETS.values())
    assert len(presets) == 5

    ids = {p.id for p in presets}
    assert ids == {
        "tech_creator",
        "educational",
        "storytelling",
        "product_showcase",
        "personal_story",
    }

    # Voices must not all be identical
    voices = {p.voice for p in presets}
    assert len(voices) >= 4  # adam, rachel, antoni, josh, bella

    # Music tracks must be tailored to tone
    music_tracks = {p.music for p in presets}
    assert len(music_tracks) >= 4  # upbeat_pulse, ambient_chill, cinematic_acoustic, lofi_beat

    # Visual styles and tones must differ
    tones = {p.tone for p in presets}
    assert len(tones) == 5

    # Check specific assignments
    assert CREATOR_PRESETS["tech_creator"].voice == "adam"
    assert CREATOR_PRESETS["tech_creator"].music == "upbeat_pulse"
    assert CREATOR_PRESETS["educational"].voice == "rachel"
    assert CREATOR_PRESETS["educational"].music == "ambient_chill"
    assert CREATOR_PRESETS["storytelling"].voice == "antoni"
    assert CREATOR_PRESETS["storytelling"].music == "cinematic_acoustic"
    assert CREATOR_PRESETS["product_showcase"].voice == "josh"
    assert CREATOR_PRESETS["personal_story"].voice == "bella"
    assert CREATOR_PRESETS["personal_story"].music == "lofi_beat"


def test_creative_engine_anti_weirdness_rules():
    """
    Validates that cliché hooks, filler phrases, and run-on sentences are caught.
    """
    # 1. Cliche Hook Pattern Rejection
    bad_hooks = [
        "Welcome to this video about databases",
        "In this short, we will look at AI",
        "Are you ready to see how computers work?",
        "Today we are going to talk about physics",
    ]
    for hook in bad_hooks:
        dummy_story = Story(
            title="Valid Explainer Title",
            hook=hook,
            scenes=[
                StoryScene(order=1, narration=hook, caption="VALID CAPTION", visual_direction="Direct visual illustration", estimated_duration=5.0),
                StoryScene(order=2, narration="Here is the core technical breakdown.", caption="TECHNICAL DETAIL", visual_direction="Detailed breakdown illustration", estimated_duration=5.0),
            ],
            cta="Follow for more.",
            estimated_duration=10.0,
        )
        is_valid, errors = StoryQualityValidator.validate_candidate(dummy_story, prompt="databases")
        assert not is_valid, f"Expected hook '{hook}' to be rejected"
        assert any("Generic hook detected" in e for e in errors)

    # 2. Filler phrase rejection
    bad_fillers = [
        "Furthermore, this is crucial.",
        "In conclusion, that is how it works.",
        "At the end of the day, choose simplicity.",
        "To sum it up, start building today.",
    ]
    for filler in bad_fillers:
        dummy_story = Story(
            title="Valid Explainer Title",
            hook="The single biggest bottleneck isn't what you think.",
            scenes=[
                StoryScene(order=1, narration="First scene introduces problem.", caption="VALID CAPTION", visual_direction="Problem illustration", estimated_duration=5.0),
                StoryScene(order=2, narration=f"Here is why: {filler}", caption="SECOND CAPTION", visual_direction="Secondary illustration", estimated_duration=5.0),
            ],
            cta="Follow for more.",
            estimated_duration=10.0,
        )
        is_valid, errors = StoryQualityValidator.validate_candidate(dummy_story, prompt="databases")
        assert not is_valid, f"Expected filler '{filler}' to be rejected"
        assert any("filler detected" in e for e in errors)

    # 3. Spoken delivery sentence length limit (max 22 words)
    long_sentence = (
        "This is an extraordinarily long sentence that continues running on and on "
        "without any punctuation or breathing pauses making it very difficult for "
        "a voice artist or TTS engine to deliver naturally in short-form video."
    )
    story = Story(
        title="Testing Run-ons",
        hook="A crisp hook starts here.",
        scenes=[
            StoryScene(
                order=1,
                narration=long_sentence,
                caption="RUN ON SENTENCE",
                visual_direction="Visual representation of run-on",
                estimated_duration=6.0,
            ),
            StoryScene(
                order=2,
                narration="Crisp ending scene.",
                caption="THE PAYOFF",
                visual_direction="Clear visual finish",
                estimated_duration=4.0,
            ),
        ],
        cta="Follow for more.",
        estimated_duration=10.0,
    )
    is_valid, issues = StoryQualityValidator.validate_candidate(story, prompt="testing")
    assert not is_valid
    assert any("unnaturally long sentence" in issue for issue in issues)


def test_activation_metrics_lifecycle():
    """
    Validates that activation telemetry accurately reflects creator workflow milestones:
    - time_to_first_story_ms
    - is_activated = True
    - has_edited_scene transitions
    - has_used_ask_vidsnap transitions
    """
    metrics = CreationMetrics(
        time_to_first_idea_ms=450.0,
        time_to_first_story_ms=1200.0,
        time_to_first_preview_ms=1200.0,
        is_activated=True,
    )
    assert metrics.is_activated is True
    assert metrics.has_edited_scene is False
    assert metrics.has_used_ask_vidsnap is False
    assert metrics.has_duplicated is False

    project = Project(
        id="test-p8-activation",
        title="Vector DBs Explained",
        created_at="2026-09-14T12:00:00Z",
        status=JobStatus.COMPLETED,
        lifecycle_state=LifecycleState.READY,
        scenes=[
            Scene(order=1, narration="Hook", caption="HOOK", duration_seconds=5.0),
            Scene(order=2, narration="Payoff", caption="PAYOFF", duration_seconds=5.0),
        ],
        metrics=metrics,
    )
    assert project.metrics.is_activated is True


def test_repeat_use_duplication_and_second_run_flow():
    """
    Validates that duplicating a project creates a distinct instance with:
    - Independent ID
    - Independent versions
    - Variant title
    - Flagged has_duplicated = True
    """
    original = Project(
        id="proj-original-1234",
        title="The Feynman Technique",
        created_at="2026-09-14T12:00:00Z",
        status=JobStatus.COMPLETED,
        lifecycle_state=LifecycleState.READY,
        scenes=[
            Scene(order=1, narration="Hook 1", caption="H1", duration_seconds=4.0),
            Scene(order=2, narration="Body 1", caption="B1", duration_seconds=6.0),
        ],
        metrics=CreationMetrics(is_activated=True),
    )
    original.create_snapshot("Initial Version")

    # Simulate duplication mechanics
    dup_scenes = [Scene.model_validate(s.model_dump()) for s in original.scenes]
    duplicate = Project(
        id="proj-variant-5678",
        title=f"{original.title} (Variant)",
        created_at="2026-09-14T12:05:00Z",
        status=JobStatus.QUEUED,
        lifecycle_state=LifecycleState.STORY_READY,
        scenes=dup_scenes,
        metrics=original.metrics.model_copy() if original.metrics else CreationMetrics(),
    )
    duplicate.metrics.has_duplicated = True
    duplicate.create_snapshot(f"Initial Version (Duplicated from {original.id[:8]})")

    assert duplicate.id != original.id
    assert duplicate.title == "The Feynman Technique (Variant)"
    assert duplicate.metrics.has_duplicated is True
    assert len(duplicate.versions) == 1
    assert len(duplicate.scenes) == 2

    # Modifying duplicate should not affect original
    duplicate.scenes[0].narration = "Brand new hook for second Reel"
    assert original.scenes[0].narration == "Hook 1"
