from typing import Optional
from pydantic import BaseModel
from app.models import Story, Scene

class CreatorPreset(BaseModel):
    id: str
    name: str
    audience: str
    tone: str
    visual_style: str
    caption_style: str
    voice: str
    music: str
    length: str
    description: str

CREATOR_PRESETS: dict[str, CreatorPreset] = {
    "tech_creator": CreatorPreset(
        id="tech_creator",
        name="Tech Explainer",
        audience="Tech Creators & Engineers",
        tone="Fast-Paced Explainer",
        visual_style="cinematic",
        caption_style="kinetic",
        voice="adam",
        music="upbeat_pulse",
        length="30s",
        description="High-momentum engineering & tech breakdown with kinetic captions and driving synthesizer score.",
    ),
    "educational": CreatorPreset(
        id="educational",
        name="Educational Concept",
        audience="Students & Learners",
        tone="Conceptual Breakdown",
        visual_style="minimal",
        caption_style="highlight",
        voice="rachel",
        music="ambient_chill",
        length="30s",
        description="Clear step-by-step concept breakdown using everyday analogies and calm focus music.",
    ),
    "storytelling": CreatorPreset(
        id="storytelling",
        name="Cinematic Story",
        audience="General Audience",
        tone="Documentary Story",
        visual_style="documentary",
        caption_style="minimal",
        voice="antoni",
        music="cinematic_acoustic",
        length="45s",
        description="Atmospheric narrative journey with personal stakes, rich visual framing, and reflective pacing.",
    ),
    "product_showcase": CreatorPreset(
        id="product_showcase",
        name="Product / Idea Launch",
        audience="Early Adopters & Customers",
        tone="Punchy Product Hook",
        visual_style="dynamic",
        caption_style="kinetic",
        voice="josh",
        music="upbeat_pulse",
        length="20s",
        description="Snappy 20s feature or idea teaser highlighting pain point, mechanism, and decisive call to action.",
    ),
    "personal_story": CreatorPreset(
        id="personal_story",
        name="Personal Reflection",
        audience="Community & Peers",
        tone="First-Person Reflection",
        visual_style="minimal",
        caption_style="highlight",
        voice="bella",
        music="lofi_beat",
        length="30s",
        description="Intimate, conversational first-person reflection ('I used to think... until this happened') with warm lo-fi score.",
    ),
}

def get_creator_preset(preset_id: str) -> Optional[CreatorPreset]:
    return CREATOR_PRESETS.get(preset_id)

def evaluate_story_qualitative(story: Story, scenes: Optional[list[Scene]] = None) -> list[str]:
    """
    Produces honest, explainable qualitative feedback points based directly on
    the concrete characteristics of the story, avoiding arbitrary numeric scores.
    """
    feedback: list[str] = []
    scenes_to_check = scenes if scenes else story.scenes

    # 1. Hook evaluation
    hook_lower = story.hook.lower()
    if any(q in hook_lower for q in ["?", "why", "how", "isn't", "aren't", "stop", "never", "what if"]):
        feedback.append("Strong opening hook with immediate tension and curiosity gap.")
    else:
        feedback.append("Opening hook clearly establishes the central topic.")

    # 2. Scene flow and pacing evaluation
    scene_count = len(scenes_to_check)
    if scene_count >= 4:
        feedback.append(f"Progression is well-paced across {scene_count} distinct narrative beats.")
    elif scene_count == 3:
        feedback.append("Compact 3-scene structure focused on core insight.")
    else:
        feedback.append("Minimalist story structure; keep visual transitions dynamic.")

    # 3. Caption conciseness evaluation
    captions = [s.caption for s in scenes_to_check if s.caption]
    if captions:
        avg_word_count = sum(len(c.split()) for c in captions) / len(captions)
        if avg_word_count <= 4:
            feedback.append("Screen captions are tight and punchy for fast mobile reading.")
        elif avg_word_count <= 7:
            feedback.append("Captions are descriptive; consider shortening for kinetic impact.")
        else:
            feedback.append("Some captions are dense; kinetic viewers benefit from shorter phrasing.")

    # 4. Repetition check across scene narrations
    words_per_scene = [set(s.narration.lower().split()) for s in scenes_to_check if s.narration]
    repeated_notable_words = set()
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "it", "this", "that"}
    for i in range(len(words_per_scene) - 1):
        intersection = (words_per_scene[i] & words_per_scene[i + 1]) - stopwords
        repeated_notable_words.update([w for w in intersection if len(w) > 4])

    if repeated_notable_words:
        sample_word = list(repeated_notable_words)[0]
        feedback.append(f"Noticeable keyword overlap between consecutive scenes ('{sample_word}').")

    # 5. Call to action / ending evaluation
    cta = story.cta or (scenes_to_check[-1].caption if scenes_to_check else "")
    if cta:
        if any(w in cta.lower() for w in ["follow", "subscribe", "build", "try", "join", "discover", "explore"]):
            feedback.append("Call to action provides a clear next step for the viewer.")
        else:
            feedback.append("Ending serves as a reflective conclusion; consider adding a direct action.")

    return feedback

def generate_alternative_hooks(topic: str, current_hook: str, domain: str = "technology") -> list[dict]:
    """
    Generates 2 distinct, high-quality alternative hooks with genuine strategic variations
    (e.g., Problem/Tension vs. Counter-intuitive curiosity) while staying faithful to the topic.
    """
    topic_clean = topic.strip().rstrip(".?!")

    if domain == "science":
        alt_1 = {
            "id": "alt_1",
            "strategy": "counterintuitive",
            "label": "Counter-Intuitive Truth",
            "hook": f"What most people assume about {topic_clean} turns out to be backwards.",
            "caption": "THE HIDDEN TRUTH",
        }
        alt_2 = {
            "id": "alt_2",
            "strategy": "curiosity_gap",
            "label": "Curiosity Gap",
            "hook": f"If you've ever wondered how {topic_clean} actually functions, here is the secret.",
            "caption": "HOW IT ACTUALLY WORKS",
        }
    elif domain == "business":
        alt_1 = {
            "id": "alt_1",
            "strategy": "problem_tension",
            "label": "High-Stakes Problem",
            "hook": f"The costliest mistake when scaling {topic_clean} happens before you even start.",
            "caption": "THE COSTLY MISTAKE",
        }
        alt_2 = {
            "id": "alt_2",
            "strategy": "bold_statement",
            "label": "Bold Provocation",
            "hook": f"Stop approaching {topic_clean} the traditional way. Here is the modern playbook.",
            "caption": "THE NEW PLAYBOOK",
        }
    else:
        # Technology / Default
        alt_1 = {
            "id": "alt_1",
            "strategy": "counterintuitive",
            "label": "The Paradigm Shift",
            "hook": f"The biggest breakthrough in {topic_clean} isn't doing more work. It's changing who does it.",
            "caption": "THE REAL BREAKTHROUGH",
        }
        alt_2 = {
            "id": "alt_2",
            "strategy": "problem_tension",
            "label": "Immediate Tension",
            "hook": f"If you're still treating {topic_clean} as optional in 2026, you're already falling behind.",
            "caption": "DON'T FALL BEHIND",
        }

    return [alt_1, alt_2]
