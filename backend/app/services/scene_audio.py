"""
VidSnap AI - Scene-Level Audio Service (Phase 7)
Provides per-scene speech synthesis caching, exact duration tracking,
and timeline concatenation.

Principles:
- Changing Scene N regenerates ONLY Scene N's audio segment
- Unaffected scenes (1..N-1, N+1..) reuse cached audio and alignment segments directly
- Exact scene durations are measured directly via ffprobe, eliminating proportional guessing
- Assembles the final raw voice track via lossless FFmpeg concatenation
"""

import json
import time
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional
from app.models import Project, Scene, CaptionSegment, CaptionWord
from app.services.audio import get_audio_duration
from app.services.ai import tts_service
from app.services.speech_alignment import SpeechAlignmentEngine

logger = logging.getLogger("vidsnap.services.scene_audio")


class SceneAudioService:
    """
    Manages scene-level audio caching and timeline concatenation.
    """

    @classmethod
    def get_cache_dir(cls, project_dir: Path) -> Path:
        cache_dir = project_dir / "audio_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @classmethod
    def compute_scene_audio_hash(cls, scene_id: str, text: str, voice: str) -> str:
        raw = f"{scene_id.strip()}:{text.strip()}:{voice.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def generate_or_reuse_scene_audio(
        cls,
        project_dir: Path,
        scene: Scene,
        voice: str,
    ) -> tuple[Path, float, list[CaptionSegment], str, bool]:
        """
        Retrieves cached audio and alignment metadata if narration and voice are unchanged.
        Otherwise, synthesizes speech for this scene and saves to cache.

        Returns: (audio_path, duration, caption_segments, alignment_source, was_cached)
        """
        cache_dir = cls.get_cache_dir(project_dir)
        narration_text = (scene.narration or scene.caption or "").strip()
        if not narration_text:
            narration_text = "Scene preview"

        hash_key = cls.compute_scene_audio_hash(scene.id, narration_text, voice)
        cached_audio = cache_dir / f"scene_{scene.order}_{hash_key}.mp3"
        cached_meta = cache_dir / f"scene_{scene.order}_{hash_key}.json"

        # Check Cache Hit
        if cached_audio.exists() and cached_meta.exists() and cached_audio.stat().st_size > 500:
            try:
                meta_data = json.loads(cached_meta.read_text(encoding="utf-8"))
                duration = float(meta_data["duration"])
                align_src = meta_data.get("alignment_source", "estimated")
                segments: list[CaptionSegment] = []
                for s_raw in meta_data.get("segments", []):
                    words = [CaptionWord(**w) for w in s_raw.get("words", [])]
                    segments.append(
                        CaptionSegment(
                            text=s_raw["text"],
                            start_time=s_raw["start_time"],
                            end_time=s_raw["end_time"],
                            words=words,
                        )
                    )
                logger.info(f"Audio cache HIT for Scene {scene.order} ({duration:.2f}s). Reusing audio.")
                return cached_audio, duration, segments, align_src, True
            except Exception as e:
                logger.warning(f"Failed loading audio cache for scene {scene.order}: {e}. Regenerating.")

        # Cache Miss: Synthesize speech for this scene
        logger.info(f"Audio cache MISS for Scene {scene.order}. Synthesizing voice with '{voice}'...")
        t0 = time.perf_counter()
        _, native_alignment = tts_service.generate_speech_with_alignment(
            text=narration_text,
            voice_key=voice,
            output_path=cached_audio,
        )
        duration = get_audio_duration(cached_audio)
        gen_ms = round((time.perf_counter() - t0) * 1000, 1)

        # Align speech for this scene
        words, segments, align_src = SpeechAlignmentEngine.align_scene(
            narration=narration_text,
            scene_duration=duration,
            audio_path=cached_audio,
            native_alignment=native_alignment,
            style="kinetic",
        )

        # Save metadata to cache
        try:
            meta_content = {
                "scene_id": scene.id,
                "order": scene.order,
                "narration": narration_text,
                "voice": voice,
                "duration": duration,
                "generation_ms": gen_ms,
                "alignment_source": align_src,
                "segments": [s.model_dump() for s in segments],
            }
            cached_meta.write_text(json.dumps(meta_content, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not write audio cache metadata for Scene {scene.order}: {e}")

        logger.info(f"Synthesized Scene {scene.order} audio ({duration:.2f}s) in {gen_ms}ms using '{align_src}'.")
        return cached_audio, duration, segments, align_src, False

    @classmethod
    def concatenate_scene_audios(cls, audio_paths: list[Path], output_path: Path) -> Path:
        """
        Concatenates multiple audio files into a single unified voice track using FFmpeg.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if len(audio_paths) == 1:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(audio_paths[0]),
                "-c:a", "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path

        # Multi-input concat filter
        cmd = ["ffmpeg", "-y"]
        filter_inputs = ""
        for idx, p in enumerate(audio_paths):
            cmd.extend(["-i", str(p)])
            filter_inputs += f"[{idx}:a]"

        filtergraph = f"{filter_inputs}concat=n={len(audio_paths)}:v=0:a=1[aout]"
        cmd.extend([
            "-filter_complex", filtergraph,
            "-map", "[aout]",
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(output_path),
        ])

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    @classmethod
    def build_project_audio_plan(
        cls,
        project: Project,
        project_dir: Path,
    ) -> tuple[Path, list[float], dict]:
        """
        Processes audio scene-by-scene:
        1. Reuses cached audio for unchanged scenes
        2. Generates TTS only for modified/new scenes
        3. Updates each scene's duration_seconds with exact ffprobe duration
        4. Offsets caption segment timestamps to global timeline
        5. Assembles final raw voice track
        """
        t_start = time.perf_counter()
        audio_paths: list[Path] = []
        scene_durations: list[float] = []
        cached_count = 0
        regenerated_count = 0
        timeline_offset = 0.0

        for scene in project.scenes:
            audio_path, duration, local_segments, align_src, was_cached = cls.generate_or_reuse_scene_audio(
                project_dir=project_dir,
                scene=scene,
                voice=project.voice,
            )
            audio_paths.append(audio_path)
            scene_durations.append(duration)
            scene.duration_seconds = duration
            scene.alignment_source = align_src

            if was_cached:
                cached_count += 1
            else:
                regenerated_count += 1

            # Offset caption segments to global timeline
            global_segments: list[CaptionSegment] = []
            for seg in local_segments:
                offset_words = [
                    CaptionWord(
                        text=w.text,
                        start_time=round(w.start_time + timeline_offset, 3),
                        end_time=round(w.end_time + timeline_offset, 3),
                        emphasized=w.emphasized,
                    )
                    for w in seg.words
                ]
                global_segments.append(
                    CaptionSegment(
                        text=seg.text,
                        start_time=round(seg.start_time + timeline_offset, 3),
                        end_time=round(seg.end_time + timeline_offset, 3),
                        words=offset_words,
                    )
                )

            scene.caption_segments = global_segments
            if global_segments:
                scene.caption_segment = global_segments[0]

            timeline_offset += duration

        # Losslessly assemble final concatenated voice file
        raw_voice_path = project_dir / "voice_raw.mp3"
        cls.concatenate_scene_audios(audio_paths, raw_voice_path)

        total_assembly_ms = round((time.perf_counter() - t_start) * 1000, 1)
        total_voice_duration = sum(scene_durations)

        telemetry = {
            "cached_scenes": cached_count,
            "regenerated_scenes": regenerated_count,
            "total_scenes": len(project.scenes),
            "assembly_ms": total_assembly_ms,
            "voice_duration": total_voice_duration,
        }

        logger.info(
            f"Project {project.id} audio assembled in {total_assembly_ms}ms: "
            f"{cached_count} cached, {regenerated_count} generated, duration: {total_voice_duration:.2f}s"
        )

        return raw_voice_path, scene_durations, telemetry
