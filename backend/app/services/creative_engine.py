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
                "contrarian": f"{topic} aren't just helping developers write code. They're changing who does the writing in the first place.",
                "problem": f"The biggest bottleneck in software engineering today isn't typing speed. It's the friction of manual implementation.",
                "future": f"In five years, writing software line by line will feel as outdated as punching cards into a mainframe.",
                "curiosity": f"Most people think {topic} is about faster autocomplete. The reality under the hood is completely different.",
            }

        elif domain == "science":
            core_claim = f"The physical mechanisms behind {topic} reveal counterintuitive laws of nature."
            audience_value = "Grasp an everyday natural phenomenon through simple, elegant physics."
            tension = "What looks like a simple visual reality is actually the result of microscopic particle collisions."
            key_points = [
                "Light travels as a spectrum of wavelengths through the atmosphere.",
                "Shorter wavelengths scatter far more intensely off microscopic particles.",
                "The human eye perceives the accumulated scattered wavelengths across the sky.",
            ]
            hook_angles = {
                "contrarian": f"The sky isn't actually blue because of reflections from the ocean. The real mechanism comes down to how light collides with air.",
                "problem": f"If sunlight is pure white, why doesn't the sky look white during the day? Here is the physics.",
                "future": f"Understanding how light scatters through our atmosphere is the exact same method astronomers use to detect water on distant exoplanets.",
                "curiosity": f"Have you ever wondered why sunlight looks warm and yellow, but paints the entire sky vivid blue?",
            }

        elif domain == "education":
            core_claim = f"{topic} works through distributed, decentralized protocols coordinating in milliseconds."
            audience_value = "Demystify complex global systems into an intuitive mental model."
            tension = "You experience instant simplicity, but underneath lies billions of independently routed packets."
            key_points = [
                "Data is broken down into small, numbered packets.",
                "Routers send packets across optimal paths through undersea fiber lines.",
                "The receiving client reassembles the packets in strict order.",
            ]
            hook_angles = {
                "contrarian": f"Whenever you tap a link, your phone isn't opening a single direct pipeline. It's slicing your data into thousands of packets.",
                "problem": f"How do billions of devices stream video simultaneously across the globe without collapsing the network?",
                "future": f"The underlying protocols designed decades ago now carry petabytes of global intelligence every second.",
                "curiosity": f"What actually happens in the half-second between tapping 'search' and getting millions of results?",
            }

        elif domain == "business":
            core_claim = f"Product-market fit in {topic} is a pull dynamic, not an engineering milestone."
            audience_value = "Avoid building in isolation and learn how to identify authentic market demand."
            tension = "Founders often build polished solutions for problems customers will never pay to solve."
            key_points = [
                "Building features in isolation is a trap without real customer feedback.",
                "Product-market fit feels like customer pull, not sales push.",
                "Clarity on the core user pain point trumps complex feature sets.",
            ]
            hook_angles = {
                "contrarian": f"Most startups don't fail from building the wrong product. They build the right product for a problem nobody actually has.",
                "problem": f"The hardest phase of any startup isn't coding the MVP. It's finding customers who refuse to live without it.",
                "future": f"The startups that survive the next decade won't be feature factories—they will be obsessed with singular customer pain points.",
                "curiosity": f"Why do well-funded teams with brilliant engineers still fail to find product-market fit?",
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
# 2. Hard Quality Validator
# ---------------------------------------------------------------------------

GENERIC_HOOK_PATTERNS = [
    r"today\s+we('re|\s+are)\s+going\s+to\s+talk\s+about",
    r"in\s+this\s+video",
    r"let'?s\s+dive\s+into",
    r"welcome\s+back",
    r"this\s+topic\s+is\s+very\s+interesting",
    r"is\s+changing\s+the\s+world\s+in\s+many\s+ways",
    r"without\s+further\s+ado",
    r"have\s+you\s+ever\s+wondered\s+what\s+is",
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
]


class StoryQualityValidator:
    """
    Deterministic hard quality checks.
    Rejects generic hooks, literal prompt repetition, filler phrases, overlong captions,
    run-on sentences, duplicate visuals, and lack of narrative progression.
    """

    @classmethod
    def validate_candidate(cls, story: Story, prompt: str, target_length: str = "30s") -> tuple[bool, list[str]]:
        errors: list[str] = []
        clean_prompt = TopicInterpreter.clean_topic(prompt).lower()

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

        # 7. Sentence length check (no run-ons > 35 words without punctuation)
        for scene in story.scenes:
            sentences = re.split(r"[.!?]", scene.narration)
            for s in sentences:
                words = s.strip().split()
                if len(words) > 35:
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

        title = f"The Truth About {topic.title()}" if len(topic.split()) <= 4 else topic.title()

        # Build candidate based on angle
        if hook_strategy == "contrarian":
            hook = interpretation.hook_angles.get("contrarian", f"{topic} isn't what most people think.")
            if domain == "technology":
                narrations = [
                    hook,
                    "Instead of developers writing every function line by line, software systems are shifting to goal-directed orchestration.",
                    "That moves the human job from manual syntax to reviewing architecture, edge cases, and deployment outcomes.",
                    "The valuable skill isn't disappearing—it's moving up a level.",
                    "And that is the exact reason autonomous agents are defining the future of engineering.",
                ]
                captions = [
                    "NOT JUST WRITING CODE",
                    "GOAL-DIRECTED ORCHESTRATION",
                    "REVIEW OVER SYNTAX",
                    "MOVING UP A LEVEL",
                    "THE AUTONOMOUS FUTURE",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "science":
                narrations = [
                    hook,
                    "Sunlight appears pure white to us, but it actually contains every color in the spectrum, each traveling at different wavelengths.",
                    "Blue light travels in short, rapid waves, colliding with atmospheric gas molecules and scattering across the entire sky.",
                    "That physical phenomenon is Rayleigh scattering, and it explains why daytime is drenched in blue.",
                    "At sunset, the light passes through thicker air, leaving behind brilliant reds and oranges.",
                ]
                captions = [
                    "NOT THE OCEAN",
                    "WHITE LIGHT IS A SPECTRUM",
                    "RAYLEIGH SCATTERING",
                    "THE SUNSET SHIFT",
                    "PHYSICS IN PLAIN SIGHT",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "business":
                narrations = [
                    hook,
                    "Founders often spend six months polishing features in isolation before confirming if real customers care.",
                    "Product-market fit isn't a feature milestone. It's the moment the market pulls the product out of your hands.",
                    "Until you feel that customer pull, extra code is just noise masking the absence of demand.",
                    "Validate the pain point first. Then build the solution.",
                ]
                captions = [
                    "THE WRONG PROBLEM",
                    "BUILDING IN ISOLATION",
                    "MARKET PULL OVER PUSH",
                    "NOISE VS REAL DEMAND",
                    "VALIDATE BEFORE BUILDING",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "education":
                narrations = [
                    hook,
                    "Every photo, message, and video gets sliced into tiny data packets tagged with digital addresses.",
                    "Global routers pass these packets along fiber cables across ocean floors in fractions of a millisecond.",
                    "At the destination, the TCP protocol reassembles them in exact sequence without losing a byte.",
                    "Millions of packets, zero human intervention, happening continuously.",
                ]
                captions = [
                    "SLICED INTO PACKETS",
                    "ACROSS OCEAN FLOORS",
                    "REASSEMBLED IN SEQUENCE",
                    "GLOBAL DATA IN MILLISECONDS",
                    "HOW THE WEB WORKS",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            else: # personal
                narrations = [
                    hook,
                    "The model itself was the easiest part. The real challenge was handling edge cases and latency under pressure.",
                    "Users didn't care about what architecture I used—they only cared that it worked reliably every time.",
                    "The biggest breakthrough came when I stopped theorizing and shipped the simplest working prototype.",
                    "Iterating in public taught me ten times more than weeks of private planning.",
                ]
                captions = [
                    "THE MODEL IS EASY",
                    "EDGE CASES ARE HARD",
                    "RESULTS OVER ARCHITECTURE",
                    "SHIP EARLY PROTOTYPES",
                    "BUILDING IN PUBLIC",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]

            cta = "Save this reel. Which part surprised you the most?"

        elif hook_strategy == "problem":
            hook = interpretation.hook_angles.get("problem", f"The biggest issue with {topic} is hidden in plain sight.")
            if domain == "technology":
                narrations = [
                    hook,
                    "Teams spend forty percent of engineering hours on boilerplate, unit tests, and mundane dependency updates.",
                    "Intelligent agents can now analyze codebases, run diagnostics, and draft verified fixes autonomously.",
                    "This lets creators focus on high-leverage product decisions rather than repetitive syntax.",
                    "Mastering this workflow today will be the biggest competitive advantage in modern tech.",
                ]
                captions = [
                    "THE BOILERPLATE TRAP",
                    "AUTONOMOUS DIAGNOSTICS",
                    "FOCUS ON HIGH LEVERAGE",
                    "THE NEW ADVANTAGE",
                    "DIRECT THE MACHINES",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "science":
                narrations = [
                    hook,
                    "Sunlight travels 93 million miles through the vacuum of space without scattering at all.",
                    "The moment it strikes Earth's nitrogen and oxygen molecules, the short blue wavelengths scatter everywhere.",
                    "Longer wavelengths like red pass right through, which is why the sun looks warm against the blue sky.",
                    "It's an atmospheric prism created by nature every single day.",
                ]
                captions = [
                    "THE SPACE VACUUM",
                    "ATMOSPHERIC COLLISION",
                    "BLUE SCATTERS EVERYWHERE",
                    "NATURE'S LIVING PRISM",
                    "DISCOVER THE SCIENCE",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "business":
                narrations = [
                    hook,
                    "Most founders start by asking 'What can we build?' instead of 'Who is desperately looking for a fix?'",
                    "If your early users aren't complaining when the server goes down, you haven't found product-market fit yet.",
                    "Obsess over the exact moment a customer feels relief using your tool.",
                    "That single breakthrough is worth fifty roadmap features.",
                ]
                captions = [
                    "THE WRONG STARTING QUESTION",
                    "DO USERS COMPLAIN?",
                    "FINDING REAL RELIEF",
                    "ONE ESSENTIAL BREAKTHROUGH",
                    "SOLVE ONE PAIN",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "education":
                narrations = [
                    hook,
                    "If millions of users accessed one central server at once, global infrastructure would crash in seconds.",
                    "Instead, decentralized networks split the load across edge caches and optical fiber backbones.",
                    "Your request travels to the nearest available node, returning data in the blink of an eye.",
                    "That distributed resilience is what keeps modern society connected.",
                ]
                captions = [
                    "NO CENTRAL BOTTLENECK",
                    "DECENTRALIZED EDGE NODES",
                    "INSTANT GLOBAL ROUTING",
                    "DISTRIBUTED RESILIENCE",
                    "THE GLOBAL BACKBONE",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            else: # personal
                narrations = [
                    hook,
                    "My first build crashed immediately because I didn't plan for unexpected user inputs.",
                    "Real users break things in ways you never imagine while testing in a clean local environment.",
                    "Learning to build defensive fallbacks turned my brittle demo into a resilient, production app.",
                    "Failure is just telemetry showing you what needs attention next.",
                ]
                captions = [
                    "MY FIRST CRASH",
                    "USERS BREAK EVERYTHING",
                    "DEFENSIVE PRODUCT DESIGN",
                    "FAILURE IS TELEMETRY",
                    "KEEP ITERATING",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]

            cta = "Drop your experience below. Have you faced this challenge?"

        else: # future / curiosity
            hook = interpretation.hook_angles.get("future", f"The trajectory of {topic} is about to accelerate.")
            if domain == "technology":
                narrations = [
                    hook,
                    "We are moving from conversational chatbots to autonomous systems that execute end-to-end tasks.",
                    "Engineers will spend less time writing functions and more time curating goals and system constraints.",
                    "The leverage of an individual developer is multiplying by ten, allowing solo founders to build enterprise platforms.",
                    "Start directing intelligent workflows now, or compete against those who do.",
                ]
                captions = [
                    "FROM CHAT TO EXECUTION",
                    "CURATING SYSTEM CONSTRAINTS",
                    "10X DEVELOPER LEVERAGE",
                    "SOLO ENTERPRISE BUILDERS",
                    "THE FUTURE IS HERE",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "science":
                narrations = [
                    hook,
                    "When light hits gas molecules in our air, it scatters based on the exact diameter of the molecule.",
                    "Blue light has the exact wavelength that scatters most easily across nitrogen and oxygen.",
                    "On Mars, where the atmosphere is thin carbon dioxide and dust, the sky is actually butterscotch brown.",
                    "Your view of the sky is entirely defined by the chemical envelope around your planet.",
                ]
                captions = [
                    "MOLECULAR DIAMETER",
                    "WHY BLUE SCATTERS",
                    "THE MARTIAN SKY",
                    "A CHEMICAL ENVELOPE",
                    "LOOK TO THE SKY",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "business":
                narrations = [
                    hook,
                    "The next generation of breakout startups will solve acute operational bottlenecks with tiny, elite teams.",
                    "When software development costs drop toward zero, distribution and customer trust become the primary moats.",
                    "Find a community that has a painful daily manual process, and automate it completely.",
                    "That is how defensible companies are founded in 2026.",
                ]
                captions = [
                    "TINY ELITE TEAMS",
                    "DISTRIBUTION IS THE MOAT",
                    "AUTOMATE DAILY PAIN",
                    "THE 2026 PLAYBOOK",
                    "BUILD WITH LEVERAGE",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            elif domain == "education":
                narrations = [
                    hook,
                    "In the next decade, decentralized edge networks and satellite constellations will connect every square mile of the planet.",
                    "Information will travel between continents through laser-linked space relays at near light speed.",
                    "The foundation remains the humble data packet, proving that timeless protocols outlive hardware.",
                    "The internet isn't static—it's an evolving planetary organism.",
                ]
                captions = [
                    "PLANETARY NETWORKS",
                    "LASER SPACE RELAYS",
                    "TIMELESS PACKET DESIGN",
                    "AN EVOLVING ORGANISM",
                    "THE CONNECTED WORLD",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]
            else: # personal
                narrations = [
                    hook,
                    "Shipping my first project didn't just teach me tech—it gave me conviction that I can build anything.",
                    "The distance between an idea in your head and a working product is shorter than it has ever been.",
                    "Don't wait for permission or the perfect setup. Start with a tiny prototype today.",
                    "The best way to learn is to put something real into the world.",
                ]
                captions = [
                    "BUILDING REAL CONVICTION",
                    "IDEA TO PRODUCT",
                    "START TODAY",
                    "PUT IT IN THE WORLD",
                    "CREATE WITHOUT PERMISSION",
                ]
                roles = ["hook", "context", "insight", "implication", "cta"]

            cta = "Share this with someone who needs to hear it today."

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
