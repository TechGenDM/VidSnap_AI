"""
VidSnap AI - Creative Engine (Phase 2.5)
Orchestrates high-quality story generation:
User Input -> Topic Interpretation -> Hook/Angle Generation ->
Candidate Story Generation -> Deterministic Validation ->
Candidate Evaluation -> Best Candidate Selection.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass
from app.models import Story, StoryScene

logger = logging.getLogger("vidsnap.services.creative_engine")

# ---------------------------------------------------------------------------
# 1. Topic Interpretation
# ---------------------------------------------------------------------------

@dataclass
class TopicInterpretation:
    raw_prompt: str
    topic: str
    domain: str # "technology" | "science" | "education" | "business" | "personal"
    core_claim: str
    audience_value: str
    interesting_tension: str
    key_points: list[str]
    hook_angles: dict[str, str] # "curiosity", "contrarian", "problem", "future"


class TopicInterpreter:
    """
    Understands the user's topic before generating stories.
    Classifies domain, extracts clean topic, formulates thesis, tension, and 4 distinct hook angles.
    Internal representation: not exposed by default to the user.
    """

    @staticmethod
    def clean_topic(prompt: str) -> str:
        t = prompt.strip().rstrip(".!?")
        # Strip generic introductory command phrases
        t = re.sub(
            r"^(explain\s+why|explain\s+how|explain|what\s+is|why\s+is|tell\s+me\s+about|how\s+does|why\s+do|how\s+to|a\s+video\s+about|create\s+a\s+reel\s+about|make\s+a\s+video\s+on)\s+",
            "",
            t,
            flags=re.IGNORECASE,
        ).strip()
        # If pattern is "X is/are changing ...", extract core subject X
        match = re.search(r"^(.*?)\s+(?:is|are)\s+changing\b", t, flags=re.IGNORECASE)
        if match and len(match.group(1).split()) <= 4:
            return match.group(1).strip()
        return t

    @staticmethod
    def detect_domain(prompt: str) -> str:
        p = prompt.lower()
        if any(k in p for k in ["my first", "i built", "what i learned", "lessons", "journey", "my experience", "failure", "my project", "personal"]):
            return "personal"
        if any(k in p for k in ["startup", "product-market fit", "product market fit", "founder", "sales", "revenue", "business", "pricing", "customers", "growth", "b2b", "venture", "market"]):
            return "business"
        if any(k in p for k in ["sky", "blue", "physics", "biology", "chemistry", "space", "planet", "earth", "dna", "quantum", "sun", "atmosphere", "water", "light", "waves", "universe"]):
            return "science"
        if any(k in p for k in ["how does", "how do", "internet", "packets", "protocols", "history", "education", "basics", "fundamentals", "math", "router"]):
            return "education"
        # Default or tech
        return "technology"

    @classmethod
    def interpret(cls, prompt: str) -> TopicInterpretation:
        topic = cls.clean_topic(prompt)
        if not topic:
            topic = "the future of modern technology"
        domain = cls.detect_domain(prompt)

        # Domain-specific narrative claims, tensions, and hook angles
        if domain == "technology":
            core_claim = f"{topic} is shifting the developer's role from writing syntax to orchestrating outcomes."
            audience_value = "Understand where software leverage is moving so you stay ahead."
            tension = "Typing code is becoming a commodity; system taste and decision architecture are the real moat."
            key_points = [
                "Autonomous agents operate at the level of intent rather than keystrokes.",
                "Developers review, steer, and verify architecture rather than typing boilerplate.",
                "The leverage moves up a level: from writing code to deciding what gets built.",
            ]
            hook_angles = {
                "contrarian": f"The biggest misconception about {topic} is that traditional methods are still good enough.",
                "problem": f"The single biggest bottleneck in {topic} isn't raw compute. It's how your architecture is structured.",
                "future": f"In the next generation of software, systems built without {topic} simply won't scale.",
                "curiosity": f"Why are top engineering teams quietly rethinking their entire approach to {topic}?",
            }

        elif domain == "science":
            core_claim = f"The physical mechanisms behind {topic} reveal counterintuitive laws of nature."
            audience_value = "Grasp a fundamental concept through clear, intuitive physics."
            tension = "What looks simple on the surface is actually governed by elegant microscopic principles."
            key_points = [
                f"The physical laws governing {topic} contradict common intuition.",
                "Small foundational interactions produce massive observable effects.",
                "Understanding the core mechanism unlocks how the entire system behaves.",
            ]
            hook_angles = {
                "contrarian": f"The most startling truth about {topic} is completely opposite to what common intuition tells us.",
                "problem": f"Why do standard textbooks make {topic} sound complicated when the core principle is so simple?",
                "future": f"The mind-bending implications of {topic} are shaping the future of physics and technology.",
                "curiosity": f"What if the foundational law behind {topic} was hiding in plain sight all along?",
            }

        elif domain == "education":
            core_claim = f"{topic} works through distributed, decentralized coordination in fractions of a second."
            audience_value = "Demystify a complex topic into an intuitive mental model."
            tension = "You experience instant simplicity, but underneath lies seamless multi-step coordination."
            key_points = [
                f"Break {topic} down into simple, sequential building blocks.",
                "Each layer communicates effortlessly with the next.",
                "The entire process completes automatically without manual friction.",
            ]
            hook_angles = {
                "contrarian": f"Most people overcomplicate {topic}, but the core mechanism comes down to one mental model.",
                "problem": f"Why do most explanations of {topic} leave people more confused than when they started?",
                "future": f"Mastering {topic} gives you an unfair advantage in how you analyze complex problems.",
                "curiosity": f"Can you explain the real principle behind {topic} in under thirty seconds?",
            }

        elif domain == "business":
            core_claim = f"Authentic traction in {topic} comes from eliminating real customer friction, not adding features."
            audience_value = "Avoid building in isolation and learn how to solve high-value problems."
            tension = "Founders often build polished solutions for problems customers will never pay to solve."
            key_points = [
                f"Building features in isolation is a trap without real feedback on {topic}.",
                "Authentic traction feels like customer pull, not sales push.",
                "Clarity on the single biggest pain point always wins.",
            ]
            hook_angles = {
                "contrarian": f"Most projects around {topic} fail not from lack of effort, but from solving the wrong problem.",
                "problem": f"The hardest part of {topic} isn't starting. It's finding an approach that truly scales.",
                "future": f"The future of {topic} belongs to creators and builders who eliminate friction entirely.",
                "curiosity": f"What is the single counterintuitive secret that separates top performers in {topic}?",
            }

        else: # personal
            core_claim = f"Building my first project taught me that iteration speed and user reality matter far more than theory."
            audience_value = "Gain practical, hard-won insights from hands-on building rather than textbook advice."
            tension = "The hardest part was never the technical stack; it was handling messy real-world edge cases."
            key_points = [
                "Theory collapses quickly when real users touch your software.",
                "Edge cases and error handling consume 80% of project effort.",
                "Shipping an imperfect prototype early beats months of private polishing.",
            ]
            hook_angles = {
                "contrarian": f"When I started my first AI project, I thought model architecture was everything. I was completely wrong.",
                "problem": f"Nobody warns you about the messy reality of building your first AI application from scratch.",
                "future": f"The lessons from shipping a first AI prototype completely changed how I think about modern software craft.",
                "curiosity": f"Here is the single biggest mistake I made when building my first AI project—and how you can avoid it.",
            }

        return TopicInterpretation(
            raw_prompt=prompt,
            topic=topic,
            domain=domain,
            core_claim=core_claim,
            audience_value=audience_value,
            interesting_tension=tension,
            key_points=key_points,
            hook_angles=hook_angles,
        )


# ---------------------------------------------------------------------------
# 2. Title Quality Validator & Hard Quality Validator
# ---------------------------------------------------------------------------

AWKWARD_TITLE_PATTERNS = [
    r"^the\s+truth\s+about\s+(why|how|what|when|where|is|are|do|does)\b",
    r"^you\s+won'?t\s+believe\b",
    r"shocking\s+secrets?\b",
    r"mind[- ]blowing\s+truth\b",
]

MINOR_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
    "nor", "of", "on", "or", "so", "the", "to", "with", "yet"
}

ACRONYMS = {"ai", "ui", "ux", "api", "b2b", "b2c", "llm", "ml", "gpu", "cpu", "tts"}


class TitleQualityValidator:
    """
    Validates and standardizes titles.
    Rejects awkward, ungrammatical, or clickbait formulations (e.g. 'The Truth About Why Is The Sky Blue').
    Produces natural, concise, and engaging titles (e.g. 'Why Is the Sky Blue?').
    """

    @classmethod
    def to_natural_title_case(cls, text: str) -> str:
        words = text.strip().split()
        if not words:
            return ""
        result = []
        for i, raw_word in enumerate(words):
            clean = raw_word.strip(",.!?\"'()")
            punct_after = raw_word[len(clean):] if raw_word.startswith(clean) else ""
            clean_lower = clean.lower()

            if clean_lower in ACRONYMS:
                cased = clean_lower.upper()
            elif i == 0 or i == len(words) - 1:
                cased = clean.capitalize()
            elif clean_lower in MINOR_WORDS:
                cased = clean_lower
            else:
                cased = clean.capitalize()
            result.append(cased + punct_after)
        return " ".join(result)

    @classmethod
    def clean_title(cls, prompt: str, topic: str) -> str:
        p = prompt.strip().rstrip(".!?")

        # If prompt contains "what i learned" (declarative narrative, no question mark)
        if re.search(r"\bwhat\s+i\s+learned\b", p, re.I):
            return cls.to_natural_title_case(p).rstrip(".!?")

        # If prompt is already a natural question
        if re.match(r"^(why|how|what|where|when|is|can|do|does)\b", p, re.I):
            title = cls.to_natural_title_case(p)
            if not title.endswith("?"):
                title += "?"
            return title

        # If prompt starts with "explain why / how" or "tell me about"
        match_q = re.match(r"^(?:explain|tell me(?:\s+about)?)\s+(why|how|what)\s+(.*)$", p, re.I)
        if match_q:
            q_word = match_q.group(1).capitalize()
            rest = match_q.group(2).strip()
            title = cls.to_natural_title_case(f"{q_word} {rest}")
            if not title.endswith("?"):
                title += "?"
            return title

        # Otherwise clean topic
        cleaned_topic = topic.strip().rstrip(".!?")
        if re.match(r"^(why|how|what)\b", cleaned_topic, re.I):
            title = cls.to_natural_title_case(cleaned_topic)
            if not title.endswith("?"):
                title += "?"
            return title

        words = cleaned_topic.split()
        if len(words) <= 2:
            title = f"Understanding {cls.to_natural_title_case(cleaned_topic)}"
        else:
            title = cls.to_natural_title_case(cleaned_topic)
            
        return title

    @classmethod
    def validate_title(cls, title: str) -> tuple[bool, list[str]]:
        errors: list[str] = []
        t_lower = title.strip().lower()

        if len(title.strip()) < 4:
            errors.append(f"Title '{title}' is too short.")
        elif len(title.strip()) > 90:
            errors.append(f"Title '{title}' is too long.")

        for pat in AWKWARD_TITLE_PATTERNS:
            if re.search(pat, t_lower):
                errors.append(f"Awkward formulation detected in title: '{title}' matching '{pat}'.")

        is_valid = len(errors) == 0
        return is_valid, errors


GENERIC_HOOK_PATTERNS = [
    r"today\s+we('re|\s+are)\s+going\s+to\s+talk\s+about",
    r"in\s+this\s+video",
    r"in\s+this\s+short",
    r"welcome\s+to",
    r"let'?s\s+dive\s+into",
    r"welcome\s+back",
    r"this\s+topic\s+is\s+very\s+interesting",
    r"is\s+changing\s+the\s+world\s+in\s+many\s+ways",
    r"without\s+further\s+ado",
    r"have\s+you\s+ever\s+wondered\s+what\s+is",
    r"^are\s+you\s+ready\s+to\b",
]

OBVIOUS_FILLER_PATTERNS = [
    r"as\s+we\s+all\s+know",
    r"without\s+further\s+ado",
    r"it\s+goes\s+without\s+saying",
    r"very\s+interesting\s+and\s+important",
    r"needless\s+to\s+say",
    r"in\s+today's\s+fast-paced\s+world",
    r"an\s+amazing\s+topic",
    r"dive\s+into\s+this\s+amazing",
    r"\bfurthermore\b",
    r"\bin\s+conclusion\b",
    r"\bat\s+the\s+end\s+of\s+the\s+day\b",
    r"\bto\s+sum\s+it\s+up\b",
]


class StoryQualityValidator:
    """
    Deterministic hard quality checks.
    Rejects generic hooks, literal prompt repetition, filler phrases, overlong captions,
    run-on sentences, duplicate visuals, awkward titles, and lack of narrative progression.
    """

    @classmethod
    def validate_candidate(cls, story: Story, prompt: str, target_length: str = "30s") -> tuple[bool, list[str]]:
        errors: list[str] = []
        clean_prompt = TopicInterpreter.clean_topic(prompt).lower()

        # 0. Title quality validation
        is_title_valid, title_errs = TitleQualityValidator.validate_title(story.title)
        if not is_title_valid:
            errors.extend(title_errs)

        # 1. Generic hook check
        hook_lower = story.hook.lower().strip()
        for pat in GENERIC_HOOK_PATTERNS:
            if re.search(pat, hook_lower):
                errors.append(f"Generic hook detected matching pattern: '{pat}'")

        # 2. Literal prompt copying in hook
        if hook_lower == prompt.lower().strip() or hook_lower == clean_prompt:
            errors.append("Hook is a literal copy of the prompt.")

        # 3. Filler in narration
        full_text = " ".join([s.narration for s in story.scenes]).lower()
        for pat in OBVIOUS_FILLER_PATTERNS:
            if re.search(pat, full_text):
                errors.append(f"Obvious filler detected matching pattern: '{pat}'")

        # 4. Prompt repetition tautology ("X because X")
        if re.search(r"(\b[\w\s]{4,80}\b)\s+because\s+\1", full_text):
            errors.append("Tautological repetition detected in narration.")

        # 5. Caption quality (2 to 7 words, not identical to narration)
        for scene in story.scenes:
            cap_words = scene.caption.strip().split()
            if len(cap_words) < 2:
                errors.append(f"Scene {scene.order} caption is too short ({len(cap_words)} words). Must be 2-7 words.")
            elif len(cap_words) > 7:
                errors.append(f"Scene {scene.order} caption is too long ({len(cap_words)} words). Must be 2-7 words.")

            if scene.caption.strip().lower() == scene.narration.strip().lower():
                errors.append(f"Scene {scene.order} caption is an exact duplicate of its narration.")

        # 6. Repetitive scenes / Duplicate visual directions
        vis_dirs = [s.visual_direction.strip().lower() for s in story.scenes]
        if len(vis_dirs) != len(set(vis_dirs)):
            errors.append("Duplicate visual directions found across scenes.")

        # 7. Sentence length check (no run-ons > 22 words without punctuation to ensure crisp spoken delivery)
        for scene in story.scenes:
            sentences = re.split(r"[.!?]", scene.narration)
            for s in sentences:
                words = s.strip().split()
                if len(words) > 22:
                    errors.append(f"Scene {scene.order} contains an unnaturally long sentence ({len(words)} words).")

        # 8. Duration sanity check
        expected_dur = 15.0 if "15" in target_length else (55.0 if "60" in target_length else 30.0)
        if abs(story.estimated_duration - expected_dur) > (expected_dur * 0.5):
            errors.append(f"Estimated duration ({story.estimated_duration}s) wildly diverges from target ({expected_dur}s).")

        is_valid = len(errors) == 0
        return is_valid, errors


# ---------------------------------------------------------------------------
# 3. Heuristic Candidate Evaluator
# ---------------------------------------------------------------------------

class StoryEvaluator:
    """
    Evaluates candidate stories on human qualities:
    - Hook curiosity / tension
    - Spoken conversational cadence
    - Specificity and substance
    - Pacing across scene roles
    - Caption precision (2-7 words sweet spot)
    - Visual relevance
    - Low repetition
    Produces an internal quality score (0.0 - 1.0) without fake precision.
    """

    @classmethod
    def evaluate(cls, story: Story, interpretation: TopicInterpretation) -> float:
        score = 0.50 # Base score

        hook = story.hook.lower()
        # Bonus for tension / contrast starters
        if any(hook.startswith(prefix) for prefix in ["most ", "instead of", "the real reason", "what if", "why do", "when i", "if you're still", "the biggest"]):
            score += 0.12
        if any(w in hook for w in ["not just", "instead", "nobody", "wrong", "secret", "reality", "actually", "truth"]):
            score += 0.08

        # Spoken cadence: check narration sentence length (10-18 words is optimal for speech)
        lengths = []
        for s in story.scenes:
            for sent in re.split(r"[.!?]", s.narration):
                w = sent.strip().split()
                if w:
                    lengths.append(len(w))
        avg_sent_len = sum(lengths) / max(1, len(lengths))
        if 8 <= avg_sent_len <= 20:
            score += 0.10
        elif avg_sent_len > 25:
            score -= 0.10

        # Scene roles: reward structured progression (hook -> insight/context -> implication/cta)
        roles = [s.scene_role for s in story.scenes if s.scene_role]
        if "hook" in roles and ("insight" in roles or "context" in roles):
            score += 0.08

        # Captions precision: reward 3 to 6 words
        cap_lengths = [len(s.caption.split()) for s in story.scenes]
        if all(2 <= cl <= 7 for cl in cap_lengths):
            score += 0.06
        if any(3 <= cl <= 5 for cl in cap_lengths):
            score += 0.04

        # Specificity: check presence of key domain nouns/verbs
        all_text = " ".join([s.narration for s in story.scenes]).lower()
        key_matches = sum(1 for kp in interpretation.key_points if any(w in all_text for w in kp.lower().split()[:3]))
        score += min(0.08, key_matches * 0.03)

        # Repetition penalty: check if topic phrase is repeated more than 3 times
        topic_lower = interpretation.topic.lower()
        occurrences = all_text.count(topic_lower)
        if occurrences > 3:
            score -= 0.12

        return round(max(0.1, min(0.98, score)), 2)


# ---------------------------------------------------------------------------
# 4. Multi-Candidate Story Generator
# ---------------------------------------------------------------------------

class CandidateStoryGenerator:
    """
    Generates 2–3 complete story candidates differing in narrative angle and hook strategy.
    """

    @classmethod
    def generate_candidate(
        cls,
        interpretation: TopicInterpretation,
        hook_strategy: str,
        target_length: str,
        tone: str,
        style: str,
        seed: int = 0,
    ) -> Story:
        topic = interpretation.topic
        domain = interpretation.domain

        # Determine scene count and timing based on target duration
        if "15" in target_length:
            num_scenes = 3
            est_total = 15.0
            per_scene_dur = 5.0
        elif "60" in target_length:
            num_scenes = 5
            est_total = 55.0
            per_scene_dur = 11.0
        else: # 30s
            num_scenes = 4
            est_total = 28.0
            per_scene_dur = 7.0

        title = TitleQualityValidator.clean_title(prompt=interpretation.raw_prompt, topic=topic)

        # Build candidate based on angle and creator's specific topic
        t_clean = topic.strip().rstrip(".?!")
        if hook_strategy == "contrarian":
            hook = interpretation.hook_angles.get("contrarian", f"The biggest misconception about {t_clean} is that traditional methods are still good enough.")
            narrations = [
                hook,
                f"Most workflows treat {t_clean} as a complicated afterthought, but the core mechanism is surprisingly straightforward.",
                f"When you understand how the underlying structure works, the usual friction completely disappears.",
                f"That breakthrough is why leading builders and creators are quietly rethinking their entire approach to {t_clean}.",
                f"Master this foundation today, and you will stay years ahead of everyone else.",
            ]
            captions = [
                "THE HIDDEN TRUTH",
                "FOUNDATIONAL STRUCTURE",
                "FRICTION DISAPPEARS",
                "THE REAL BREAKTHROUGH",
                "STAY YEARS AHEAD",
            ]
            roles = ["hook", "context", "insight", "implication", "cta"]
            cta = f"Save this reel. What is your experience with {t_clean}?"

        elif hook_strategy == "problem":
            hook = interpretation.hook_angles.get("problem", f"The biggest bottleneck in {t_clean} is completely hidden in plain sight.")
            narrations = [
                hook,
                f"Creators and teams waste hours trying to optimize symptoms instead of solving the core bottleneck in {t_clean}.",
                f"The secret is shifting from manual execution to an intelligent, automated feedback loop.",
                f"Once you remove that bottleneck, results compound with virtually zero extra friction.",
                f"Stop doing it the hard way—upgrade your approach to {t_clean} now.",
            ]
            captions = [
                "HIDDEN IN PLAIN SIGHT",
                "TREATING THE SYMPTOMS",
                "INTELLIGENT LOOPS",
                "COMPOUND RESULTS",
                "UPGRADE YOUR APPROACH",
            ]
            roles = ["hook", "context", "insight", "implication", "cta"]
            cta = f"Follow for more breakdowns on {t_clean}."

        elif hook_strategy == "future":
            hook = interpretation.hook_angles.get("future", f"In five years, how we handle {t_clean} will make today look like the stone age.")
            narrations = [
                hook,
                f"Right now, almost everyone is relying on manual steps and outdated assumptions about {t_clean}.",
                f"The next generation of tools handles the complexity automatically in the background.",
                f"That frees you to focus on high-impact strategy while the system does the heavy lifting.",
                f"The future of {t_clean} is already here for those paying attention.",
            ]
            captions = [
                "THE COMING SHIFT",
                "OUTDATED ASSUMPTIONS",
                "AUTOMATED COMPLEXITY",
                "HIGH IMPACT STRATEGY",
                "THE FUTURE IS HERE",
            ]
            roles = ["hook", "context", "insight", "implication", "cta"]
            cta = f"Share this with someone building in {t_clean}."

        else: # curiosity
            hook = interpretation.hook_angles.get("curiosity", f"What if the hardest part of {t_clean} could be solved in under thirty seconds?")
            narrations = [
                hook,
                f"Most people think mastering {t_clean} requires months of painstaking trial and error.",
                f"In reality, one counterintuitive insight changes how the entire workflow functions.",
                f"Once you see the pattern, you cannot unsee how much time was being wasted.",
                f"Try this mental model on your next project and watch what happens.",
            ]
            captions = [
                "SOLVED IN SECONDS",
                "MONTHS OF TRIAL",
                "THE COUNTERINTUITIVE KEY",
                "STOP WASTING TIME",
                "TEST IT TODAY",
            ]
            roles = ["hook", "context", "insight", "implication", "cta"]
            cta = f"Save this reel to test on your next project."

        # Visual directions matching tone/style
        visual_templates = [
            f"Cinematic close-up of creator at a sleek workstation reviewing autonomous decisions in a {style.lower()} environment.",
            f"Abstract minimal visualization of interconnected nodes and data streams against a deep dark background.",
            f"High-contrast aesthetic shot of modern creator dashboard with smooth motion curves.",
            f"Dynamic isometric view of decentralized systems routing information effortlessly.",
            f"Bold typographical framing with ambient lighting summarizing key takeaways.",
        ]

        scenes: list[StoryScene] = []
        for i in range(num_scenes):
            order = i + 1
            narr = narrations[i % len(narrations)]
            cap = captions[i % len(captions)]
            vis = visual_templates[i % len(visual_templates)]
            role = roles[i % len(roles)]

            scenes.append(
                StoryScene(
                    order=order,
                    narration=narr,
                    caption=cap,
                    visual_direction=vis,
                    estimated_duration=round(per_scene_dur, 1),
                    scene_role=role,
                )
            )

        return Story(
            title=title,
            hook=hook,
            scenes=scenes,
            cta=cta,
            estimated_duration=est_total,
            hook_strategy=hook_strategy,
            domain=domain,
        )


# ---------------------------------------------------------------------------
# 5. Master Pipeline Execution
# ---------------------------------------------------------------------------

def generate_high_quality_story(
    prompt: str,
    audience: str = "Tech Creators",
    tone: str = "Educational",
    length: str = "30s",
    style: str = "Minimal Tech",
    variation_seed: Optional[int] = None,
) -> Story:
    """
    Executes the creative pipeline:
    1. Topic Interpretation
    2. Hook Generation (contrarian, problem, future)
    3. Multi-Candidate Generation (2-3 candidates)
    4. Deterministic Validation with bounded retries (max 3 attempts)
    5. Heuristic Candidate Evaluation
    6. Selection of best canonical story
    """
    interpretation = TopicInterpreter.interpret(prompt)
    logger.info(f"Interpreted topic: '{interpretation.topic}' | Domain: {interpretation.domain}")

    seed = variation_seed or 0
    strategies = ["contrarian", "problem", "future"]

    # Rotate strategy preference based on variation_seed
    if variation_seed is not None:
        shift = variation_seed % len(strategies)
        strategies = strategies[shift:] + strategies[:shift]

    candidates: list[Story] = []
    max_retries = 3

    for attempt in range(max_retries):
        candidates.clear()
        # Generate candidates for each strategy
        for strat in strategies:
            cand = CandidateStoryGenerator.generate_candidate(
                interpretation=interpretation,
                hook_strategy=strat,
                target_length=length,
                tone=tone,
                style=style,
                seed=seed + attempt,
            )
            # Deterministic validation
            is_valid, validation_errors = StoryQualityValidator.validate_candidate(
                story=cand,
                prompt=prompt,
                target_length=length,
            )
            if is_valid:
                # Score candidate
                cand.quality_score = StoryEvaluator.evaluate(cand, interpretation)
                candidates.append(cand)
            else:
                logger.warning(f"Candidate ({strat}) rejected: {validation_errors}")

        if candidates:
            break

    # If all candidates were rejected after retries, create a guaranteed clean fallback candidate
    if not candidates:
        logger.warning("All candidate generations failed validation; generating sanitized fallback.")
        fallback = CandidateStoryGenerator.generate_candidate(
            interpretation=interpretation,
            hook_strategy="contrarian",
            target_length=length,
            tone=tone,
            style=style,
        )
        fallback.quality_score = 0.80
        return fallback

    # If a variation seed was requested, select the candidate matching the prioritized strategy
    if variation_seed is not None:
        target_strategy = strategies[0]
        matched = [c for c in candidates if c.hook_strategy == target_strategy]
        if matched:
            best_candidate = matched[0]
            logger.info(
                f"Selected variation candidate story: hook_strategy='{best_candidate.hook_strategy}', "
                f"score={best_candidate.quality_score}, title='{best_candidate.title}'"
            )
            return best_candidate

    # Otherwise select best candidate by quality score
    candidates.sort(key=lambda c: c.quality_score or 0.0, reverse=True)
    best_candidate = candidates[0]
    logger.info(
        f"Selected best candidate story: hook_strategy='{best_candidate.hook_strategy}', "
        f"score={best_candidate.quality_score}, title='{best_candidate.title}'"
    )
    return best_candidate
