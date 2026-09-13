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
        """
        Generates MP3 speech file from text.
        Tries ElevenLabs first if API key is configured.
        Falls back to local macOS high-quality speech synthesis if ElevenLabs fails or key is missing.
        """
        voice_info = VOICE_MAP.get(voice_key.lower(), VOICE_MAP["adam"])
        voice_id = voice_info["id"]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.client:
            try:
                logger.info(f"Generating voice with ElevenLabs (Voice: {voice_info['name']})...")
                audio_stream = self.client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id="eleven_turbo_v2_5",
                    output_format="mp3_44100_128", # Studio grade 44.1kHz 128kbps
                )
                with open(output_path, "wb") as f:
                    for chunk in audio_stream:
                        if chunk:
                            f.write(chunk)
                logger.info(f"ElevenLabs speech saved successfully to {output_path}")
                return output_path
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed ({e}). Falling back to local TTS engine...")

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
            return output_path
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
            return output_path

tts_service = TTSProvider()
