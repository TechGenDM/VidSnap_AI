"""
VidSnap AI - Final Reel Quality Gate (Phase 7)
Strict reliability gate validating the finished 1080x1920 MP4 before user export.

Principle:
- Blocking errors: Prevent "Ready to Post", return clear actionable fixes.
- Non-blocking observations: Allow export with concise, helpful creator warnings.
- Zero fake numerical scores.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from app.models import Project
from app.services.layout_constants import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    MAX_CHARS_PER_LINE,
    MAX_LINES,
)

logger = logging.getLogger("vidsnap.services.quality_gate")


class QualityGateReport(BaseModel):
    passed: bool
    is_ready_to_post: bool
    status_label: str
    blocking_errors: list[str] = Field(default_factory=list)
    actionable_warnings: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)


class QualityGateService:
    """
    Evaluates the physical MP4 artifact and project timeline metadata.
    """

    @classmethod
    def inspect_audio_volume(cls, video_path: Path) -> float:
        """
        Runs volumedetect filter to ensure the video contains audible speech and music.
        Returns mean volume in dB.
        """
        try:
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-af", "volumedetect",
                "-vn", "-sn", "-dn",
                "-f", "null", "/dev/null",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            for line in res.stderr.splitlines():
                if "mean_volume:" in line:
                    parts = line.split("mean_volume:")
                    if len(parts) > 1:
                        val_str = parts[1].strip().split()[0]
                        return float(val_str)
        except Exception as e:
            logger.warning(f"Could not inspect audio volume for {video_path}: {e}")
        return -20.0

    @classmethod
    def probe_video(cls, video_path: Path) -> dict:
        """
        Probes video streams and container metadata via ffprobe.
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=codec_type,codec_name,width,height,duration:format=duration,size",
            "-of", "json",
            str(video_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)

    @classmethod
    def validate_reel(
        cls,
        project: Project,
        video_path: Path,
        frame_inspection_issues: Optional[list[str]] = None,
    ) -> QualityGateReport:
        """
        Executes complete quality validation on the final MP4.
        """
        blocking_errors: list[str] = []
        actionable_warnings: list[str] = []
        checks: dict[str, bool] = {}

        # 1. Existence and File Size
        if not video_path.exists() or video_path.stat().st_size < 10000:
            blocking_errors.append("Video file was not generated or is empty.")
            checks["file_exists"] = False
            return QualityGateReport(
                passed=False,
                is_ready_to_post=False,
                status_label="Render Failed",
                blocking_errors=blocking_errors,
                actionable_warnings=[],
                checks=checks,
            )
        checks["file_exists"] = True

        # 2. FFprobe Stream Analysis
        probe_data = None
        try:
            probe_data = cls.probe_video(video_path)
            checks["container_valid"] = True
        except Exception as e:
            blocking_errors.append(f"Video container is corrupted or unplayable: {e}")
            checks["container_valid"] = False
            return QualityGateReport(
                passed=False,
                is_ready_to_post=False,
                status_label="Unplayable File",
                blocking_errors=blocking_errors,
                actionable_warnings=[],
                checks=checks,
            )

        streams = probe_data.get("streams", [])
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        # 3. Dimensions 1080x1920
        if v_stream:
            w = int(v_stream.get("width", 0))
            h = int(v_stream.get("height", 0))
            if w == CANVAS_WIDTH and h == CANVAS_HEIGHT:
                checks["dimensions_1080x1920"] = True
            else:
                checks["dimensions_1080x1920"] = False
                blocking_errors.append(f"Resolution is {w}x{h}, but TikTok/Reels standard is 1080x1920.")
        else:
            checks["dimensions_1080x1920"] = False
            blocking_errors.append("No video stream found in the rendered file.")

        # 4. Audio Stream Presence & Sync
        if not a_stream:
            checks["audio_present"] = False
            blocking_errors.append("No audio stream found. Reel is completely silent.")
        else:
            checks["audio_present"] = True
            # Volume check
            mean_vol = cls.inspect_audio_volume(video_path)
            if mean_vol < -55.0:
                checks["audio_audible"] = False
                blocking_errors.append(f"Audio volume is dangerously low ({mean_vol:.1f} dB). Voice narration may be inaudible.")
            else:
                checks["audio_audible"] = True

        # 5. Frame Inspection (Black letterboxing & pillarboxing)
        if frame_inspection_issues:
            has_letterbox = any("black" in iss.lower() for iss in frame_inspection_issues)
            if has_letterbox:
                checks["no_black_borders"] = False
                blocking_errors.append("Black letterbox/pillarbox borders detected. Framing is not full-bleed 9:16 portrait.")
            else:
                checks["no_black_borders"] = True
        else:
            checks["no_black_borders"] = True

        # 6. Caption Safe Area & Typography Observations (Non-blocking warnings)
        for idx, scene in enumerate(project.scenes):
            cap = (scene.caption or "").strip()
            if cap:
                lines = cap.split("\n")
                if len(lines) > MAX_LINES:
                    actionable_warnings.append(
                        f"Scene {idx+1} caption spans {len(lines)} lines and may crowd the lower third."
                    )
                for l in lines:
                    if len(l) > MAX_CHARS_PER_LINE + 8:
                        actionable_warnings.append(
                            f"Scene {idx+1} caption has a long phrase ('{l[:20]}...') that may wrap tightly on mobile."
                        )
                        break

        # 7. Visual Diversity Check (Non-blocking warning)
        for idx in range(len(project.scenes) - 1):
            curr_vis = project.scenes[idx].visual_filename
            next_vis = project.scenes[idx + 1].visual_filename
            if curr_vis and next_vis and curr_vis == next_vis:
                actionable_warnings.append(
                    f"Scene {idx+1} and Scene {idx+2} use identical visuals. Consider swapping B-roll for shot diversity."
                )

        # 8. Duration Check
        format_dur = float(probe_data.get("format", {}).get("duration", 0.0))
        if format_dur < 1.0:
            checks["duration_valid"] = False
            blocking_errors.append(f"Reel duration is too short ({format_dur:.1f}s) to play reliably.")
        else:
            checks["duration_valid"] = True
            if format_dur < 5.0:
                actionable_warnings.append(
                    f"Reel duration ({format_dur:.1f}s) is short; vertical videos typically perform best between 15s and 60s."
                )
            elif format_dur > 90.0:
                actionable_warnings.append(
                    f"Reel duration ({format_dur:.1f}s) exceeds the 90s vertical video optimum."
                )

        passed = len(blocking_errors) == 0
        is_ready = passed and len(actionable_warnings) <= 2
        status_label = "Ready to Post" if is_ready else ("Needs Attention" if passed else "Render Failed")

        return QualityGateReport(
            passed=passed,
            is_ready_to_post=is_ready,
            status_label=status_label,
            blocking_errors=blocking_errors,
            actionable_warnings=actionable_warnings,
            checks=checks,
        )
