import subprocess
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger("vidsnap.audio")

MUSIC_CATALOG = {
    "ambient_chill": {
        "id": "ambient_chill",
        "title": "Ambient Chill",
        "genre": "Atmospheric",
        "filename": "1.mp3",
    },
    "upbeat_pulse": {
        "id": "upbeat_pulse",
        "title": "Upbeat Pulse",
        "genre": "Energetic Electronic",
        "filename": "2.mp3",
    },
    "lofi_beat": {
        "id": "lofi_beat",
        "title": "Lo-Fi Dream",
        "genre": "Chillhop",
        "filename": "3.mp3",
    },
}

def get_available_music() -> list[dict]:
    return list(MUSIC_CATALOG.values())

def get_audio_duration(file_path: Path) -> float:
    """
    Returns exact duration of an audio or video file in seconds using ffprobe.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    duration_str = result.stdout.strip()
    try:
        duration = float(duration_str)
        return max(duration, 0.1)
    except ValueError:
        logger.warning(f"Could not parse duration '{duration_str}', defaulting to 5.0")
        return 5.0

def mix_voice_and_music(
    voice_path: Path,
    music_key: Optional[str],
    output_path: Path,
    music_volume: float = 0.14,
) -> Path:
    """
    Mixes voice narration with background music.
    Ducks background music beneath speech and fades out music smoothly at narration end.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_voice_duration = get_audio_duration(voice_path)
    total_duration = raw_voice_duration + 0.4

    music_info = MUSIC_CATALOG.get(music_key.lower()) if music_key else None
    if not music_info and music_key:
        alias_map = {
            "calm_focus": "ambient_chill",
            "energetic_beat": "upbeat_pulse",
            "ambient_flow": "lofi_beat",
            "ambient_chill": "ambient_chill",
            "upbeat_pulse": "upbeat_pulse",
            "lofi_beat": "lofi_beat",
        }
        mapped_key = alias_map.get(music_key.lower().replace(".mp3", ""))
        if mapped_key:
            music_info = MUSIC_CATALOG.get(mapped_key)

    music_file = settings.SONGS_DIR / music_info["filename"] if music_info else None
    if (not music_file or not music_file.exists()) and settings.SONGS_DIR.exists():
        available = list(settings.SONGS_DIR.glob("*.mp3"))
        if available:
            music_file = available[0]

    # If no music or music file missing, pad voice with 0.4s natural tail
    if not music_file or not music_file.exists():
        cmd = [
            "ffmpeg", "-y",
            "-i", str(voice_path),
            "-filter_complex", "[0:a]volume=1.0,apad=pad_dur=0.4[aout]",
            "-map", "[aout]",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_duration:.3f}",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    # Smooth fade out for background music in the last 1.5 seconds
    fade_start = max(0.0, total_duration - 1.5)

    # Filtergraph:
    # 1. Voice with 0.4s tail pad
    # 2. Ducked music looped with 1.5s fadeout
    # 3. amix duration=first (stops when padded voice stops)
    filtergraph = (
        f"[0:a]volume=1.0,apad=pad_dur=0.4[voice];"
        f"[1:a]volume={music_volume},afade=t=out:st={fade_start:.2f}:d=1.5[music];"
        f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_path),
        "-stream_loop", "-1", "-i", str(music_file),
        "-filter_complex", filtergraph,
        "-map", "[aout]",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_duration:.3f}",
        str(output_path),
    ]

    logger.info(f"Mixing voice ({raw_voice_duration:.2f}s + 0.4s pad) with music '{music_info['title']}' (fadeout at {fade_start:.2f}s)...")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
