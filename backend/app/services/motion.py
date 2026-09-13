"""
VidSnap AI - Motion Engine (Phase 3)
Generates subtle, smooth, deterministic, and portrait-safe camera motion
filtergraphs for FFmpeg.
Supported Presets:
- slow_zoom_in: subtle 1.0 -> 1.08 zoom centered on key tension
- slow_zoom_out: subtle 1.08 -> 1.0 zoom revealing broader perspective
- pan_left: subtle horizontal sweep right -> left
- pan_right: subtle horizontal sweep left -> right
- vertical_drift: subtle vertical drift
- static_hold: crisp, steady framing
"""

import logging
from typing import Optional

logger = logging.getLogger("vidsnap.services.motion")

SUPPORTED_MOTIONS = {
    "slow_zoom_in",
    "slow_zoom_out",
    "pan_left",
    "pan_right",
    "vertical_drift",
    "static_hold",
}


class MotionEngine:
    """
    Constructs FFmpeg filtergraphs for camera motion.
    Guarantees 1080x1920 (9:16 portrait) output with zero stretching and zero black borders.
    """

    DEFAULT_FPS: int = 30
    DEFAULT_WIDTH: int = 1080
    DEFAULT_HEIGHT: int = 1920
    SUPPORTED_MOTIONS = SUPPORTED_MOTIONS

    @classmethod
    def get_supported_motions(cls) -> list[str]:
        return sorted(list(SUPPORTED_MOTIONS))

    @classmethod
    def normalize_motion(cls, motion: Optional[str]) -> str:
        if not motion:
            return "slow_zoom_in"
        m = motion.strip().lower()
        if m in SUPPORTED_MOTIONS:
            return m
        # Map common synonyms
        if "zoom_in" in m:
            return "slow_zoom_in"
        if "zoom_out" in m:
            return "slow_zoom_out"
        if "pan_l" in m or "left" in m:
            return "pan_left"
        if "pan_r" in m or "right" in m:
            return "pan_right"
        if "drift" in m or "vertical" in m:
            return "vertical_drift"
        return "static_hold"

    @classmethod
    def build_motion_filter(
        cls,
        motion: str,
        duration: float,
        fps: int = 30,
        target_width: int = 1080,
        target_height: int = 1920,
    ) -> str:
        """
        Builds a high-quality video filter string applying camera motion to an image input.
        Scales first to a 1.5x canvas (1620x2880) so zoompan crop produces crystal-sharp anti-aliased output.
        """
        norm_motion = cls.normalize_motion(motion)
        total_frames = max(1, int(duration * fps))
        d = total_frames

        # High-resolution portrait canvas pre-scale: ensures source fills 9:16 frame without bars
        prescale_w = int(target_width * 1.5) # 1620
        prescale_h = int(target_height * 1.5) # 2880
        prescale = f"scale={prescale_w}:{prescale_h}:force_original_aspect_ratio=increase,crop={prescale_w}:{prescale_h}"

        if norm_motion == "slow_zoom_in":
            # Subtle 1.0 -> 1.08 zoom centered
            z_expr = f"1.0+0.08*(on/{d})"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        elif norm_motion == "slow_zoom_out":
            # Subtle 1.08 -> 1.0 zoom centered
            z_expr = f"1.08-0.08*(on/{d})"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        elif norm_motion == "pan_left":
            # 1.08 zoom margin, pan smoothly right to left
            z_expr = "1.08"
            x_expr = f"(iw-iw/zoom)*(1.0-(on/{d}))"
            y_expr = "ih/2-(ih/zoom/2)"

        elif norm_motion == "pan_right":
            # 1.08 zoom margin, pan smoothly left to right
            z_expr = "1.08"
            x_expr = f"(iw-iw/zoom)*(on/{d})"
            y_expr = "ih/2-(ih/zoom/2)"

        elif norm_motion == "vertical_drift":
            # 1.08 zoom margin, drift smoothly vertically
            z_expr = "1.08"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = f"(ih-ih/zoom)*(0.2+0.6*(on/{d}))"

        else: # static_hold
            # Subtle steady framing
            z_expr = "1.04"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        zoompan = (
            f"zoompan=z='{z_expr}':"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"d={d}:"
            f"s={target_width}x{target_height}:"
            f"fps={fps}"
        )

        return f"{prescale},{zoompan},setsar=1"
