"""
VidSnap AI - Speech Alignment Engine (Phase 4)
Produces speech-synchronized word-level timestamps and kinetic caption segments.

Priority:
1. Native ElevenLabs provider timestamps when available (alignment_source: 'native')
2. Acoustic silence/energy alignment via FFmpeg (alignment_source: 'transcription')
3. Syllable-weighted deterministic timing fallback (alignment_source: 'estimated')

Never claims word-level synchronization when using only estimated timings.
"""

import re
import logging
import subprocess
from pathlib import Path
from typing import Optional
from app.models import CaptionWord, CaptionSegment

logger = logging.getLogger("vidsnap.services.speech_alignment")

# Common words to exclude from auto-emphasis
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "for", "in", "on",
    "at", "by", "to", "of", "up", "with", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "can", "could", "will",
    "would", "shall", "should", "may", "might", "must", "it", "its", "that", "this",
    "they", "their", "them", "we", "our", "us", "you", "your", "he", "she", "his", "her"
}


def count_syllables(word: str) -> int:
    """Estimates the number of syllables in an English word."""
    cleaned = re.sub(r"[^a-zA-Z]", "", word).lower()
    if not cleaned:
        return 1
    if len(cleaned) <= 3:
        return 1

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in cleaned:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    # Adjust for common silent endings
    if cleaned.endswith("e") and not cleaned.endswith("le") and len(cleaned) > 2:
        if not cleaned.endswith("ee"):
            count = max(1, count - 1)
    if cleaned.endswith("ed") and not (cleaned.endswith("ted") or cleaned.endswith("ded")):
        count = max(1, count - 1)

    return max(1, count)


def detect_audio_speech_intervals(audio_path: Path) -> list[tuple[float, float]]:
    """
    Detects active speech intervals in audio using FFmpeg silencedetect.
    Returns a list of (start, end) timestamps for active speech sections.
    """
    if not audio_path.exists():
        return []

    cmd = [
        "ffmpeg",
        "-i", str(audio_path),
        "-af", "silencedetect=noise=-30dB:d=0.15",
        "-f", "null",
        "-",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        silence_starts: list[float] = []
        silence_ends: list[float] = []

        for line in res.stderr.splitlines():
            if "silence_start:" in line:
                m = re.search(r"silence_start:\s*([\d\.]+)", line)
                if m:
                    silence_starts.append(float(m.group(1)))
            elif "silence_end:" in line:
                m = re.search(r"silence_end:\s*([\d\.]+)", line)
                if m:
                    silence_ends.append(float(m.group(1)))

        # Convert silences into active speech segments
        from app.services.audio import get_audio_duration
        total_duration = get_audio_duration(audio_path)

        speech_segments: list[tuple[float, float]] = []
        cursor = 0.0

        for i in range(len(silence_starts)):
            s_start = silence_starts[i]
            s_end = silence_ends[i] if i < len(silence_ends) else s_start + 0.2
            if s_start > cursor + 0.1:
                speech_segments.append((cursor, s_start))
            cursor = max(cursor, s_end)

        if cursor < total_duration - 0.1:
            speech_segments.append((cursor, total_duration))

        return speech_segments
    except Exception as e:
        logger.warning(f"Audio speech interval detection failed: {e}")
        return []


class SpeechAlignmentEngine:
    """
    Aligns narration text with spoken audio at the word and kinetic phrase level.
    """

    @classmethod
    def align_from_native_timestamps(
        cls,
        text: str,
        alignment_data: dict,
        total_duration: float,
    ) -> list[CaptionWord]:
        """
        Parses native ElevenLabs character-level timestamps into CaptionWord objects.
        """
        characters = alignment_data.get("characters", [])
        start_times = alignment_data.get("character_start_times_seconds", [])
        end_times = alignment_data.get("character_end_times_seconds", [])

        if not characters or not start_times or not end_times:
            return []

        words: list[CaptionWord] = []
        current_chars: list[str] = []
        word_start: Optional[float] = None
        word_end: Optional[float] = None

        for idx, char in enumerate(characters):
            t_start = start_times[idx] if idx < len(start_times) else 0.0
            t_end = end_times[idx] if idx < len(end_times) else t_start + 0.05

            if char.isspace():
                if current_chars and word_start is not None and word_end is not None:
                    w_text = "".join(current_chars).strip()
                    if w_text:
                        is_emph = cls._should_emphasize(w_text)
                        words.append(
                            CaptionWord(
                                text=w_text,
                                start_time=round(min(word_start, total_duration), 3),
                                end_time=round(min(word_end, total_duration), 3),
                                emphasized=is_emph,
                            )
                        )
                    current_chars = []
                    word_start = None
                    word_end = None
            else:
                if word_start is None:
                    word_start = t_start
                word_end = t_end
                current_chars.append(char)

        if current_chars and word_start is not None and word_end is not None:
            w_text = "".join(current_chars).strip()
            if w_text:
                is_emph = cls._should_emphasize(w_text)
                words.append(
                    CaptionWord(
                        text=w_text,
                        start_time=round(min(word_start, total_duration), 3),
                        end_time=round(min(word_end, total_duration), 3),
                        emphasized=is_emph,
                    )
                )

        return words

    @classmethod
    def align_from_acoustic_analysis(
        cls,
        text: str,
        audio_path: Path,
        total_duration: float,
    ) -> list[CaptionWord]:
        """
        Aligns words using detected acoustic speech boundaries combined with
        phonetic syllable modeling.
        """
        raw_words = [w.strip() for w in text.split() if w.strip()]
        if not raw_words:
            return []

        speech_segments = detect_audio_speech_intervals(audio_path)
        if not speech_segments:
            speech_start = 0.08
            speech_end = max(speech_start + 0.5, total_duration - 0.15)
        else:
            speech_start = speech_segments[0][0]
            speech_end = min(speech_segments[-1][1], total_duration)

        speech_window = max(0.4, speech_end - speech_start)

        # Calculate phonetic syllable weights
        weights = []
        for w in raw_words:
            s_count = count_syllables(w)
            char_len = len(re.sub(r"[^a-zA-Z0-9]", "", w))
            # Syllables account for 65% of weight, length 35%
            weight = (s_count * 0.65) + (char_len * 0.08)
            # Add pause weight for trailing punctuation
            if w.endswith((",", ";")):
                weight += 0.4
            elif w.endswith((".", "!", "?")):
                weight += 0.7
            weights.append(weight)

        total_weight = sum(weights) if sum(weights) > 0 else 1.0

        words: list[CaptionWord] = []
        t_cursor = speech_start

        for idx, w in enumerate(raw_words):
            allocated_dur = (weights[idx] / total_weight) * speech_window
            word_dur = max(0.12, allocated_dur * 0.88)
            w_start = t_cursor
            w_end = min(total_duration, w_start + word_dur)

            words.append(
                CaptionWord(
                    text=w,
                    start_time=round(w_start, 3),
                    end_time=round(w_end, 3),
                    emphasized=cls._should_emphasize(w),
                )
            )
            t_cursor += allocated_dur

        return words

    @classmethod
    def align_deterministic_fallback(
        cls,
        text: str,
        total_duration: float,
    ) -> list[CaptionWord]:
        """
        Deterministic syllable-weighted fallback when audio analysis is unavailable.
        Strictly valid, non-overlapping, and bounded within total_duration.
        """
        raw_words = [w.strip() for w in text.split() if w.strip()]
        if not raw_words:
            return []

        safe_start = 0.05
        safe_duration = max(0.4, total_duration - 0.15)

        weights = [max(0.5, (count_syllables(w) * 0.7) + (len(w) * 0.06)) for w in raw_words]
        total_weight = sum(weights) if sum(weights) > 0 else 1.0

        words: list[CaptionWord] = []
        cursor = safe_start

        for idx, w in enumerate(raw_words):
            alloc = (weights[idx] / total_weight) * safe_duration
            w_dur = max(0.12, alloc * 0.85)
            w_start = cursor
            w_end = min(total_duration, w_start + w_dur)

            words.append(
                CaptionWord(
                    text=w,
                    start_time=round(w_start, 3),
                    end_time=round(w_end, 3),
                    emphasized=cls._should_emphasize(w),
                )
            )
            cursor += alloc

        return words

    @classmethod
    def build_kinetic_segments(
        cls,
        words: list[CaptionWord],
        style: str = "kinetic",
    ) -> list[CaptionSegment]:
        """
        Groups aligned words into short, kinetic 2-4 word reading phrases.
        """
        if not words:
            return []

        segments: list[CaptionSegment] = []
        chunk_size = 3
        idx = 0

        while idx < len(words):
            # Look ahead for punctuation boundary (comma, period)
            end_idx = min(idx + chunk_size, len(words))
            for look in range(idx, end_idx):
                if words[look].text.endswith((",", ";", ".", "!", "?")):
                    end_idx = look + 1
                    break

            chunk = words[idx:end_idx]
            if chunk:
                seg_text = " ".join([w.text for w in chunk])
                emphasis = [w.text for w in chunk if w.emphasized]
                segments.append(
                    CaptionSegment(
                        text=seg_text,
                        start_time=chunk[0].start_time,
                        end_time=chunk[-1].end_time,
                        words=chunk,
                        emphasis_words=emphasis,
                        style=style,
                    )
                )
            idx = end_idx

        return segments

    @classmethod
    def align_scene(
        cls,
        narration: str,
        scene_duration: float,
        audio_path: Optional[Path] = None,
        native_alignment: Optional[dict] = None,
        style: str = "kinetic",
    ) -> tuple[list[CaptionWord], list[CaptionSegment], str]:
        """
        Main entry point for scene alignment:
        Returns (words, segments, alignment_source)
        """
        if not narration.strip():
            return [], [], "estimated"

        alignment_source = "estimated"
        words: list[CaptionWord] = []

        # Tier 1: Native Provider Timestamps
        if native_alignment:
            try:
                words = cls.align_from_native_timestamps(
                    narration, native_alignment, scene_duration
                )
                if words:
                    alignment_source = "native"
            except Exception as e:
                logger.warning(f"Failed parsing native provider timestamps: {e}")

        # Tier 2: Acoustic Speech/Silence Alignment
        if not words and audio_path and audio_path.exists():
            try:
                words = cls.align_from_acoustic_analysis(
                    narration, audio_path, scene_duration
                )
                if words:
                    alignment_source = "transcription"
            except Exception as e:
                logger.warning(f"Acoustic audio alignment failed: {e}")

        # Tier 3: Deterministic Syllable Fallback
        if not words:
            words = cls.align_deterministic_fallback(narration, scene_duration)
            alignment_source = "estimated"

        # Validation & Clamping
        words = cls._validate_and_clamp_words(words, scene_duration)

        # Build kinetic phrase segments
        segments = cls.build_kinetic_segments(words, style=style)

        return words, segments, alignment_source

    @classmethod
    def _should_emphasize(cls, word: str) -> bool:
        """Determines if a word should receive visual emphasis."""
        clean = re.sub(r"[^a-zA-Z0-9]", "", word)
        if not clean or clean.lower() in STOP_WORDS:
            return False
        # All caps acronyms like AI, API, LLM, 10X
        if clean.isupper() and len(clean) >= 2:
            return True
        # Numbers like 10, 100, 2026
        if any(c.isdigit() for c in clean):
            return True
        # Polysyllabic substantive terms
        if len(clean) >= 6:
            return True
        return False

    @classmethod
    def _validate_and_clamp_words(
        cls,
        words: list[CaptionWord],
        max_duration: float,
    ) -> list[CaptionWord]:
        """Ensures non-overlapping, strictly positive, bounded timestamps."""
        validated: list[CaptionWord] = []
        last_end = 0.0

        for w in words:
            start = max(0.0, max(w.start_time, last_end))
            end = min(max_duration, max(start + 0.08, w.end_time))
            if start >= max_duration:
                break
            validated.append(
                CaptionWord(
                    text=w.text,
                    start_time=round(start, 3),
                    end_time=round(end, 3),
                    emphasized=w.emphasized,
                )
            )
            last_end = end

        return validated
