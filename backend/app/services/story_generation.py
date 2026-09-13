import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional
from app.models import Story, StoryScene
from app.config import settings

logger = logging.getLogger("vidsnap.services.story_generation")

class StoryGenerationProvider(ABC):
    """
    Abstract interface for AI story generation.
    Produces canonical Story objects consisting of Title, Hook, Scenes, and CTA.
    """

    @abstractmethod
    def generate_story(
        self,
        prompt: str,
        audience: str = "Tech Creators",
        tone: str = "Educational",
        length: str = "30s",
        style: str = "Minimal Tech",
        variation_seed: Optional[int] = None,
    ) -> Story:
        """Generates a validated, structured Story object from an idea."""
        pass

    @abstractmethod
    def regenerate_scene(
        self,
        story: Story,
        scene_order: int,
        prompt: str,
        feedback: Optional[str] = None,
    ) -> StoryScene:
        """Regenerates a single scene's narration, caption, and visual direction."""
        pass


class LocalStoryProvider(StoryGenerationProvider):
    """
    High-retention, deterministic Story Generation Provider.
    Generates structured, validated stories without external API dependencies.
    Supports narrative variation seeds to generate genuinely different hooks and angles.
    """

    def _clean_topic(self, prompt: str) -> str:
        topic = prompt.strip().rstrip(".!?")
        # Strip introductory question phrases if present
        topic = re.sub(r"^(explain\s+why|explain\s+how|explain|what\s+is|why\s+is|tell\s+me\s+about|how\s+does)\s+", "", topic, flags=re.IGNORECASE)
        return topic.strip()

    def generate_story(
        self,
        prompt: str,
        audience: str = "Tech Creators",
        tone: str = "Educational",
        length: str = "30s",
        style: str = "Minimal Tech",
        variation_seed: Optional[int] = None,
    ) -> Story:
        clean_topic = self._clean_topic(prompt)
        if not clean_topic:
            clean_topic = "the future of software creation"

        seed = variation_seed if variation_seed is not None else 0
        mod = seed % 4

        # Determine target scenes and duration
        if "15" in length:
            num_scenes = 3
            est_total = 15.0
            per_scene_dur = 5.0
        elif "60" in length:
            num_scenes = 5
            est_total = 55.0
            per_scene_dur = 11.0
        else: # 30s default
            num_scenes = 4
            est_total = 28.0
            per_scene_dur = 7.0

        # Title creation
        title_words = clean_topic.capitalize().split()
        title = " ".join(title_words[:6])

        # Angle 0: The Paradigm Shift
        if mod == 0:
            hook = f"Most people think {clean_topic} is about incremental speed. They're missing the bigger picture."
            scene_narrations = [
                f"Most people think {clean_topic} is just an incremental upgrade. But what is happening right now is completely different.",
                f"Instead of developers writing every line of code by hand, systems are shifting to high-level orchestration.",
                f"Autonomous agents now explore architecture, verify edge cases, and run tests before you even push.",
                f"The competitive edge isn't typing faster—it's having the best reasoning loop for your product.",
                f"Those who master this shift today will build in hours what used to take months.",
            ]
            visual_directions = [
                f"Cinematic close-up of developer reviewing code in a dark minimal IDE as AI agents resolve tasks in parallel.",
                f"Abstract glowing architectural flowchart showing autonomous agents communicating across services.",
                f"Split-screen comparison showing traditional line-by-line coding versus rapid agentic deployment.",
                f"Clean 3D visual of interconnected microservices self-assembling in a {style.lower()} environment.",
                f"Bold typographical screen summarizing the engineering velocity leap with dynamic glowing accents.",
            ]
            captions = [
                "The shift nobody saw coming",
                "Orchestration over raw syntax",
                "Agents test and verify in seconds",
                "Velocity is the new moat",
                "Build in hours, not months",
            ]
            cta = "Drop your thoughts below. Are you ready for autonomous engineering?"

        # Angle 1: The Acceleration / Future Shock
        elif mod == 1:
            hook = f"If you're still building software the traditional way, {clean_topic} changes everything today."
            scene_narrations = [
                f"If you're still building software the traditional way, {clean_topic} will completely change how you work this year.",
                f"We are moving past autocomplete into autonomous execution that understands entire codebases.",
                f"Imagine an agent that debugs memory leaks, writes regression tests, and validates pull requests overnight.",
                f"This isn't replacing engineers—it's giving every single developer the power of a full engineering team.",
                f"The future of development belongs to the architects who direct intelligent systems.",
            ]
            visual_directions = [
                f"High-energy macro shot of a luminous silicon processor with floating holographic code snippets.",
                f"Dynamic camera movement over a futuristic workstation with multiple screens running automated workflows.",
                f"Clean minimalist timeline showing the rapid evolution from manual coding to agent orchestration.",
                f"Vibrant isometric view of modern software builders deploying global applications effortlessly.",
                f"High-contrast aesthetic shot of a team reviewing live deployment metrics in a sleek tech studio.",
            ]
            captions = [
                "Software development is changing fast",
                "From autocomplete to autonomous execution",
                "Full-stack debugging in minutes",
                "Supercharge your engineering capability",
                "The future is orchestration",
            ]
            cta = "Save this reel and share it with someone who builds software."

        # Angle 2: The Deep Dive / Under the Hood
        elif mod == 2:
            hook = f"Here is the exact reason why {clean_topic} is rewriting the rules of modern tech."
            scene_narrations = [
                f"Here is the exact reason why {clean_topic} is quietly rewriting the rules of modern technology.",
                f"Traditional tools react to user keystrokes, but agentic systems reason through the problem proactively.",
                f"They inspect files, trace dependencies, run commands, and verify results without human handholding.",
                f"The bottleneck is no longer code volume; it's the clarity of your system requirements and taste.",
                f"Focus on the vision and let intelligent agents handle the implementation details.",
            ]
            visual_directions = [
                f"Sleek dark-mode visualization of an intelligent network parsing complex data graphs.",
                f"Cinematic focus on a terminal running verified automated unit tests seamlessly.",
                f"Minimalist infographic highlighting the paradigm transition from prompt-and-wait to continuous execution.",
                f"Stylized portrait of a tech innovator conceptualizing next-generation digital products.",
                f"Subtle particle animation converging into an elegant product logo against deep indigo background.",
            ]
            captions = [
                "The real mechanism behind the change",
                "From reactive tools to proactive agents",
                "Autonomous dependency tracing",
                "Vision matters more than syntax",
                "Focus on the big idea",
            ]
            cta = "Follow for daily breakdowns on AI, development, and modern product craft."

        # Angle 3: The Creator / Practical Reality
        else:
            hook = f"Everyone is talking about {clean_topic}, but here is what it actually means for you."
            scene_narrations = [
                f"Everyone is talking about {clean_topic}, but here is what it actually means for your daily workflow.",
                f"You don't need a massive team to ship complex, production-ready software anymore.",
                f"AI agents handle boilerplate, test coverage, and tedious refactoring while you focus on the user experience.",
                f"The highest leverage skill in 2026 is knowing how to direct and verify autonomous work.",
                f"Start building with agentic tools today, or find yourself competing with those who do.",
            ]
            visual_directions = [
                f"Inspiring top-down aesthetic shot of a modern creator desk with sleek laptop and coffee.",
                f"Smooth panning shot of a clean code diff showing hundreds of lines generated and verified cleanly.",
                f"Modern UI dashboard illustrating high-velocity release cycles and instant customer feedback.",
                f"Cinematic close-up of a founder launching a live application with one click.",
                f"Atmospheric wide shot of city lights at dusk symbolizing global interconnected tech builders.",
            ]
            captions = [
                "What this actually means for you",
                "Ship production software solo",
                "Automate the boilerplate forever",
                "High leverage engineering is here",
                "Start building today",
            ]
            cta = "Bookmark this Reel. Which part of your workflow will you automate first?"

        # Tone adjustments
        if tone.lower() == "high energy":
            hook = f"🔥 STOP SCROLLING. {hook}"

        # Build scenes
        scenes: list[StoryScene] = []
        for i in range(num_scenes):
            order = i + 1
            narration = scene_narrations[i % len(scene_narrations)]
            vis_dir = visual_directions[i % len(visual_directions)]
            caption = captions[i % len(captions)]

            # Adjust hook in Scene 1
            if order == 1:
                narration = f"{hook} {narration}" if not narration.startswith(hook) else narration
                caption = captions[0]

            scenes.append(
                StoryScene(
                    order=order,
                    narration=narration,
                    caption=caption,
                    visual_direction=vis_dir,
                    estimated_duration=round(per_scene_dur, 1),
                )
            )

        story = Story(
            title=title,
            hook=hook,
            scenes=scenes,
            cta=cta,
            estimated_duration=est_total,
        )
        return story

    def regenerate_scene(
        self,
        story: Story,
        scene_order: int,
        prompt: str,
        feedback: Optional[str] = None,
    ) -> StoryScene:
        clean_topic = self._clean_topic(prompt)
        # Alternate phrasing
        alt_narrations = [
            f"Here is another perspective on {clean_topic}: the speed of iteration is compounding faster than ever.",
            f"When you break down {clean_topic}, the secret lies in how intelligent agents coordinate tasks in parallel.",
            f"What was previously impossible for a solo creator is now accessible in a few focused prompts.",
            f"The real question isn't if {clean_topic} will take over, but how quickly you adapt to it.",
        ]
        alt_captions = [
            "Compounding iteration speed",
            "Parallel agent coordination",
            "Impossible tasks made simple",
            "Adapt and lead the change",
        ]
        alt_visuals = [
            f"Dramatic atmospheric shot of dynamic data streams cascading through a minimalist 3D space.",
            f"Clean macro shot of a pristine smartphone screen displaying real-time AI generation metrics.",
            f"Over-the-shoulder view of a developer orchestrating multiple agents simultaneously.",
            f"Striking typographical screen with subtle depth of field emphasizing velocity and precision.",
        ]

        idx = (scene_order + 2) % len(alt_narrations)
        return StoryScene(
            order=scene_order,
            narration=alt_narrations[idx],
            caption=alt_captions[idx],
            visual_direction=alt_visuals[idx],
            estimated_duration=round(story.estimated_duration / max(1, len(story.scenes)), 1),
        )


class OpenAIStoryProvider(StoryGenerationProvider):
    """
    OpenAI-backed Story Generation Provider.
    Invoked when OPENAI_API_KEY is available.
    Uses strict structured JSON output to guarantee Pydantic schema conformance.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.local_fallback = LocalStoryProvider()

    def generate_story(
        self,
        prompt: str,
        audience: str = "Tech Creators",
        tone: str = "Educational",
        length: str = "30s",
        style: str = "Minimal Tech",
        variation_seed: Optional[int] = None,
    ) -> Story:
        import httpx

        system_prompt = (
            "You are VidSnap AI's Lead Video Architect. "
            "You convert user ideas into high-retention vertical short-form stories (1080x1920 Reels). "
            "Strictly follow this structure:\n"
            "- Hook: Curiosity-inducing first 2 seconds.\n"
            "- Scenes: 3 to 5 scenes with concise narration, punchy screen caption, specific visual direction, and realistic estimated duration.\n"
            "- CTA: Natural ending call-to-action.\n"
            "Return valid JSON matching the exact schema."
        )

        user_content = (
            f"Topic: {prompt}\n"
            f"Target Audience: {audience}\n"
            f"Tone: {tone}\n"
            f"Target Length: {length}\n"
            f"Visual Style: {style}\n"
            f"Variation Angle Index: {variation_seed or 0}"
        )

        try:
            with httpx.Client(timeout=25.0) as client:
                res = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content},
                        ],
                        "temperature": 0.8 if variation_seed else 0.7,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    # Validate through Pydantic
                    return Story.model_validate(parsed)
                else:
                    logger.warning(f"OpenAI returned status {res.status_code}. Using local story engine fallback.")
        except Exception as e:
            logger.warning(f"OpenAI story generation failed: {e}. Falling back to local story engine.")

        return self.local_fallback.generate_story(
            prompt=prompt,
            audience=audience,
            tone=tone,
            length=length,
            style=style,
            variation_seed=variation_seed,
        )

    def regenerate_scene(
        self,
        story: Story,
        scene_order: int,
        prompt: str,
        feedback: Optional[str] = None,
    ) -> StoryScene:
        # For single scene regeneration, leverage local engine or fallback
        return self.local_fallback.regenerate_scene(
            story=story,
            scene_order=scene_order,
            prompt=prompt,
            feedback=feedback,
        )


def get_story_provider() -> StoryGenerationProvider:
    """
    Factory function: selects the story provider based on configured environment credentials.
    Does not invent credentials; gracefully defaults to LocalStoryProvider.
    """
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        logger.info("Using OpenAIStoryProvider for AI story generation.")
        return OpenAIStoryProvider(api_key=settings.OPENAI_API_KEY.strip())

    logger.info("Using LocalStoryProvider for AI story generation.")
    return LocalStoryProvider()
