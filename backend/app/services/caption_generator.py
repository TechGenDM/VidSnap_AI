"""
VidSnap AI - ASS Caption Generator (Phase 4)
Renders kinetic, speech-synchronized word-level captions formatted for 9:16 mobile viewing.

Styles:
- kinetic: Words appear in progressive phrase reveals synchronized to speech
- emphasis: Key terms receive bold vibrant gold/cyan styling
- highlight: Active spoken word receives vibrant cyan highlight

Safe for FFmpeg:
- Full escaping of special characters, quotes, and Unicode
- Strict ASS syntax with centisecond precision
- Mobile safe margins (Y=78%, bottom margin 380) avoiding TikTok/Reels UI overlay
"""

import re
import logging
from pathlib import Path
from app.models import CaptionSegment, CaptionWord

logger = logging.getLogger("vidsnap.services.caption_generator")

# Colors in BGR ASS Hex: &HAABBGGRR
COLOR_WHITE = "&H00FFFFFF"
COLOR_CYAN_ACCENT = "&H00FFFF00"     # Vibrant Electric Cyan in BGR
COLOR_GOLD_ACCENT = "&H0000D7FF"     # Warm Gold in BGR
COLOR_BLACK_OUTLINE = "&H00000000"   # Crisp black outline
COLOR_SHADOW = "&H80000000"          # 50% transparent shadow


def format_ass_time(seconds: float) -> str:
    """Formats float seconds into ASS timestamp format: H:MM:SS.cc"""
    sec = max(0.0, float(seconds))
    hours = int(sec // 3600)
    minutes = int((sec % 3600) // 60)
    secs = int(sec % 60)
    centis = int(round((sec - int(sec)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def escape_ass_text(text: str) -> str:
    """
    Safely escapes text for ASS subtitle format.
    Prevents script injection or broken filter syntax.
    """
    # Replace backslashes first
    safe = text.replace("\\", "\\\\")
    # Replace curly braces
    safe = safe.replace("{", "\\{").replace("}", "\\}")
    # Replace newlines with ASS line break
    safe = safe.replace("\r\n", "\\N").replace("\n", "\\N")
    return safe


class ASSCaptionGenerator:
    """
    Generates Advanced SubStation Alpha (.ass) subtitle files for video compositing.
    """

    @classmethod
    def generate_ass_file(
        cls,
        segments: list[CaptionSegment],
        output_path: Path,
        scene_offset: float = 0.0,
        style: str = "kinetic",
    ) -> Path:
        """
        Builds a complete ASS subtitle file from a list of CaptionSegments.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        header = [
            "[Script Info]",
            "Title: VidSnap AI Kinetic Captions",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "WrapStyle: 2",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            # Default style: 52pt bold, white text, 3.5px black outline, 2px shadow, centered at bottom margin 380
            f"Style: Default,Arial,52,{COLOR_WHITE},{COLOR_CYAN_ACCENT},{COLOR_BLACK_OUTLINE},{COLOR_SHADOW},-1,0,0,0,100,100,0,0,1,3.5,2.0,2,60,60,380,1",
            # Emphasis style: 54pt bold gold
            f"Style: Emphasis,Arial,54,{COLOR_GOLD_ACCENT},{COLOR_CYAN_ACCENT},{COLOR_BLACK_OUTLINE},{COLOR_SHADOW},-1,0,0,0,100,100,0,0,1,4.0,2.0,2,60,60,380,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        events: list[str] = []

        for seg in segments:
            seg_start = max(0.0, seg.start_time - scene_offset)
            seg_end = max(seg_start + 0.1, seg.end_time - scene_offset)

            if not seg.words:
                # Segment without word breakdown: show full phrase with safe escaping
                text_esc = escape_ass_text(seg.text)
                t_start = format_ass_time(seg_start)
                t_end = format_ass_time(seg_end)
                events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{text_esc}")
                continue

            # Word-level kinetic rendering
            if style == "kinetic":
                # Progressive reveal per word within the segment
                for w_idx, word in enumerate(seg.words):
                    w_start = max(seg_start, word.start_time - scene_offset)
                    # Next word start or segment end
                    w_end = seg_end
                    if w_idx + 1 < len(seg.words):
                        next_start = seg.words[w_idx + 1].start_time - scene_offset
                        w_end = max(w_start + 0.05, next_start)

                    if w_end <= w_start:
                        w_end = w_start + 0.1

                    t_start_str = format_ass_time(w_start)
                    t_end_str = format_ass_time(w_end)

                    # Build phrase with active word highlighted
                    line_parts = []
                    for idx_inner, inner_word in enumerate(seg.words):
                        clean_w = escape_ass_text(inner_word.text)
                        if idx_inner == w_idx:
                            # Currently active word: Vibrant Cyan + extra bold
                            line_parts.append(f"{{\\c{COLOR_CYAN_ACCENT}\\b1}}{clean_w}{{\\c{COLOR_WHITE}\\b0}}")
                        elif idx_inner < w_idx:
                            # Spoken words: Solid white
                            if inner_word.emphasized:
                                line_parts.append(f"{{\\c{COLOR_GOLD_ACCENT}\\b1}}{clean_w}{{\\c{COLOR_WHITE}\\b0}}")
                            else:
                                line_parts.append(clean_w)
                        else:
                            # Upcoming words: Slightly dimmed or hidden
                            line_parts.append(f"{{\\alpha&H60&}}{clean_w}{{\\alpha&H00&}}")

                    phrase_text = " ".join(line_parts)
                    events.append(f"Dialogue: 0,{t_start_str},{t_end_str},Default,,0,0,0,,{phrase_text}")

            elif style == "emphasis":
                # Emphasized words colored in gold
                t_start_str = format_ass_time(seg_start)
                t_end_str = format_ass_time(seg_end)
                line_parts = []
                for word in seg.words:
                    clean_w = escape_ass_text(word.text)
                    if word.emphasized:
                        line_parts.append(f"{{\\c{COLOR_GOLD_ACCENT}\\b1}}{clean_w}{{\\c{COLOR_WHITE}\\b0}}")
                    else:
                        line_parts.append(clean_w)
                phrase_text = " ".join(line_parts)
                events.append(f"Dialogue: 0,{t_start_str},{t_end_str},Default,,0,0,0,,{phrase_text}")

            else: # "highlight"
                # Standard phrase with active highlight during word windows
                for w_idx, word in enumerate(seg.words):
                    w_start = max(seg_start, word.start_time - scene_offset)
                    w_end = seg_end if w_idx + 1 == len(seg.words) else max(w_start + 0.05, seg.words[w_idx + 1].start_time - scene_offset)

                    t_start_str = format_ass_time(w_start)
                    t_end_str = format_ass_time(w_end)

                    line_parts = []
                    for idx_inner, inner_word in enumerate(seg.words):
                        clean_w = escape_ass_text(inner_word.text)
                        if idx_inner == w_idx:
                            line_parts.append(f"{{\\c{COLOR_CYAN_ACCENT}\\b1}}{clean_w}{{\\c{COLOR_WHITE}\\b0}}")
                        else:
                            line_parts.append(clean_w)
                    phrase_text = " ".join(line_parts)
                    events.append(f"Dialogue: 0,{t_start_str},{t_end_str},Default,,0,0,0,,{phrase_text}")

        full_content = "\n".join(header + events) + "\n"
        output_path.write_text(full_content, encoding="utf-8")
        logger.info(f"Generated ASS subtitles with {len(events)} events at {output_path}")
        return output_path
