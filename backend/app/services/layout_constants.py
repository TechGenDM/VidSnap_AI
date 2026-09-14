"""
VidSnap AI - Shared Layout Constants & Rule Engine (Phase 7)
Establishes canonical 1080x1920 mobile portrait layout rules shared
between FFmpeg ASS subtitles and the companion phone preview.

Guarantees:
- Safe margins (avoiding TikTok / Reels status bar, account info, and interaction buttons)
- Clean word wrapping with bounded characters per line
- Word-level emphasis coloring (Cyan active word, Gold emphasis, White spoken)
"""

# Canvas Dimensions
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
ASPECT_RATIO = "9:16"

# Mobile Safe Areas (percentages of canvas)
# Top 10.4% (200px) is reserved for phone notch / app header
SAFE_TOP_MARGIN_PCT = 0.104
SAFE_TOP_PX = int(CANVAS_HEIGHT * SAFE_TOP_MARGIN_PCT)

# Bottom 19.8% (380px) is reserved for TikTok/Reels caption box, music tag, and nav bar
SAFE_BOTTOM_MARGIN_PCT = 0.198
SAFE_BOTTOM_PX = int(CANVAS_HEIGHT * SAFE_BOTTOM_MARGIN_PCT)

# Left and Right 5.5% (60px) safe margins
SAFE_MARGIN_X_PCT = 0.055
SAFE_MARGIN_X_PX = int(CANVAS_WIDTH * SAFE_MARGIN_X_PCT)

# Caption Typography Rules
FONT_FAMILY = "Arial"
FONT_SIZE_PT = 52  # ~4.8% of canvas width
OUTLINE_WIDTH_PX = 3.5
SHADOW_DEPTH_PX = 2.0

# Word Wrapping Constraints
MAX_CHARS_PER_LINE = 28
MAX_WORDS_PER_LINE = 5
MAX_LINES = 3

# Hex & ASS Color Palettes
COLOR_WHITE = "#FFFFFF"
COLOR_CYAN_ACCENT = "#00F0FF"
COLOR_GOLD_ACCENT = "#FFD700"
COLOR_BLACK_OUTLINE = "#000000"


def wrap_caption_safe(
    text: str,
    max_chars: int = MAX_CHARS_PER_LINE,
    max_words: int = MAX_WORDS_PER_LINE,
) -> str:
    """
    Wraps caption text to prevent horizontal overflow on 1080px portrait canvas.
    Balances line lengths to avoid orphan single words.
    """
    words = text.strip().split()
    if not words:
        return ""

    lines: list[str] = []
    current_line: list[str] = []
    current_length = 0

    for word in words:
        word_len = len(word)
        # Check if adding this word violates word count or character limit
        if current_line and (len(current_line) >= max_words or (current_length + 1 + word_len) > max_chars):
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_len
        else:
            current_line.append(word)
            current_length += (1 + word_len) if current_length > 0 else word_len

    if current_line:
        lines.append(" ".join(current_line))

    # Balance lines if last line is an awkward single short word and previous line has >= 3 words
    if len(lines) >= 2 and len(lines[-1].split()) == 1 and len(lines[-2].split()) >= 3:
        prev_words = lines[-2].split()
        orphan_word = lines[-1]
        moved_word = prev_words.pop()
        lines[-2] = " ".join(prev_words)
        lines[-1] = f"{moved_word} {orphan_word}"

    return "\n".join(lines)
