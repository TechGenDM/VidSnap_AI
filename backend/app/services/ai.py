import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger("vidsnap.ai")

VOICE_MAP = {
    "adam": {
        "id": "pNInz6obpgDQGcFmaJgB",
        "name": "Adam",
        "gender": "Male",
        "accent": "Deep & Narrative",
        "macos_voice": "Alex",
    },
    "rachel": {
        "id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel",
        "gender": "Female",
        "accent": "Warm & Engaging",
        "macos_voice": "Samantha",
    },
    "josh": {
        "id": "TxGEqnHWrfWFTfGW9XjX",
        "name": "Josh",
        "gender": "Male",
        "accent": "Young & Energetic",
        "macos_voice": "Fred",
    },
    "antoni": {
        "id": "ErXwobaYiN019PkySvjV",
        "name": "Antoni",
        "gender": "Male",
        "accent": "Thoughtful & Crisp",
        "macos_voice": "Daniel",
    },
}

def get_available_voices() -> list[dict]:
    return [
        {
            "id": k,
            "name": v["name"],
            "gender": v["gender"],
            "accent": v["accent"],
            "description": f"{v['gender']} • {v['accent']}",
        }
        for k, v in VOICE_MAP.items()
    ]

class TTSProvider:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.client = None
        if self.api_key:
            try:
                from elevenlabs.client import ElevenLabs
                self.client = ElevenLabs(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize ElevenLabs client: {e}")

    def generate_speech(self, text: str, voice_key: str, output_path: Path) -> Path:
        out_path, _ = self.generate_speech_with_alignment(text, voice_key, output_path)
        return out_path

    def generate_speech_with_alignment(
        self, text: str, voice_key: str, output_path: Path
    ) -> tuple[Path, Optional[dict]]:
        """
        Generates MP3 speech file from text, capturing native provider alignment timestamps if available.
        Tries ElevenLabs convert_with_timestamps first if API key is configured.
        Falls back to local macOS high-quality speech synthesis if ElevenLabs fails or key is missing.
        """
        import base64
        voice_info = VOICE_MAP.get(voice_key.lower(), VOICE_MAP["adam"])
        voice_id = voice_info["id"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        native_alignment = None

        if self.client:
            try:
                logger.info(f"Generating voice with ElevenLabs timestamps (Voice: {voice_info['name']})...")
                ts_resp = self.client.text_to_speech.convert_with_timestamps(
                    voice_id=voice_id,
                    text=text,
                    model_id="eleven_turbo_v2_5",
                    output_format="mp3_44100_128",
                )
                if hasattr(ts_resp, "audio_base_64") and ts_resp.audio_base_64:
                    audio_bytes = base64.b64decode(ts_resp.audio_base_64)
                    output_path.write_bytes(audio_bytes)
                    if hasattr(ts_resp, "alignment") and ts_resp.alignment:
                        align_obj = ts_resp.alignment
                        native_alignment = {
                            "characters": getattr(align_obj, "characters", []),
                            "character_start_times_seconds": getattr(align_obj, "character_start_times_seconds", []),
                            "character_end_times_seconds": getattr(align_obj, "character_end_times_seconds", []),
                        }
                    logger.info(f"ElevenLabs speech with timestamps saved successfully to {output_path}")
                    return output_path, native_alignment
            except Exception as e:
                logger.warning(f"ElevenLabs TTS with timestamps failed ({e}). Falling back to local TTS engine...")

        # Fallback Engine (macOS 'say' command converted to MP3 via ffmpeg)
        logger.info(f"Using local TTS fallback (Voice: {voice_info['macos_voice']})...")
        temp_aiff = output_path.with_suffix(".aiff")
        try:
            # Generate AIFF
            subprocess.run(
                ["say", "-v", voice_info["macos_voice"], "-o", str(temp_aiff), text],
                check=True,
                capture_output=True,
            )
            # Convert to MP3
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(temp_aiff),
                    "-c:a", "libmp3lame",
                    "-b:a", "128k",
                    "-ar", "44100",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
            temp_aiff.unlink(missing_ok=True)
            return output_path, None
        except Exception as e:
            temp_aiff.unlink(missing_ok=True)
            logger.error(f"Fallback TTS failed: {e}. Generating tone fallback...")
            # Emergency fallback: generate a silent/subtle audio tone so the video pipeline still succeeds
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "5",
                    "-c:a", "libmp3lame",
                    "-b:a", "128k",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
            return output_path, None

tts_service = TTSProvider()
