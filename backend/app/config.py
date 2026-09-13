import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project Root is the repository root
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    APP_NAME: str = "VidSnap AI"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Base directories
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MEDIA_DIR: Path = PROJECT_ROOT / "media"
    UPLOADS_DIR: Path = PROJECT_ROOT / "media" / "uploads"
    REELS_DIR: Path = PROJECT_ROOT / "media" / "reels"
    THUMBNAILS_DIR: Path = PROJECT_ROOT / "media" / "thumbnails"
    SONGS_DIR: Path = PROJECT_ROOT / "media" / "songs"
    TEMPLATES_DIR: Path = PROJECT_ROOT / "media" / "templates"
    
    # API Secrets
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Video & Audio defaults
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    VIDEO_FPS: int = 30
    DEFAULT_VOICE_ID: str = "pNInz6obpgDQGcFmaJgB" # Adam
    
    # Security
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".m4a", ".aac"}

    class Config:
        env_file = PROJECT_ROOT / ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
for d in [
    settings.DATA_DIR,
    settings.MEDIA_DIR,
    settings.UPLOADS_DIR,
    settings.REELS_DIR,
    settings.THUMBNAILS_DIR,
    settings.SONGS_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
