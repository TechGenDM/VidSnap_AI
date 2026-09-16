import os
from pathlib import Path
from typing import Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project Root is the repository root
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    APP_NAME: str = "VidSnap AI"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Base directories (support persistent volume overrides via env)
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MEDIA_DIR: Path = PROJECT_ROOT / "media"
    
    # Subdirectories derived dynamically from MEDIA_DIR
    UPLOADS_DIR: Path = PROJECT_ROOT / "media" / "uploads"
    REELS_DIR: Path = PROJECT_ROOT / "media" / "reels"
    THUMBNAILS_DIR: Path = PROJECT_ROOT / "media" / "thumbnails"
    SONGS_DIR: Path = PROJECT_ROOT / "media" / "songs"
    TEMPLATES_DIR: Path = PROJECT_ROOT / "media" / "templates"
    CACHE_DIR: Path = PROJECT_ROOT / "media" / "cache"
    AI_ASSETS_DIR: Path = PROJECT_ROOT / "media" / "cache" / "ai_visuals"
    
    # CORS Origins (allow comma-separated string or list)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ]
    
    # API Secrets
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    POLLINATIONS_API_KEY: str = ""
    POLLINATIONS_IMAGE_MODEL: str = "flux"
    
    # Video & Audio defaults
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    VIDEO_FPS: int = 30
    DEFAULT_VOICE_ID: str = "pNInz6obpgDQGcFmaJgB"  # Adam
    
    # Security
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".m4a", ".aac"}

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean.startswith("[") and v_clean.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v_clean)
                    if isinstance(parsed, list):
                        return [str(o).strip() for o in parsed if str(o).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v_clean.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def derive_subdirectories(self) -> "Settings":
        # If DATA_DIR is overridden to a custom location and MEDIA_DIR is still default, nest MEDIA_DIR inside DATA_DIR
        if self.DATA_DIR != (PROJECT_ROOT / "data") and self.MEDIA_DIR == (PROJECT_ROOT / "media"):
            object.__setattr__(self, "MEDIA_DIR", self.DATA_DIR / "media")

        # Align subdirectories to MEDIA_DIR if MEDIA_DIR is set to custom mount path
        object.__setattr__(self, "UPLOADS_DIR", self.MEDIA_DIR / "uploads")
        object.__setattr__(self, "REELS_DIR", self.MEDIA_DIR / "reels")
        object.__setattr__(self, "THUMBNAILS_DIR", self.MEDIA_DIR / "thumbnails")
        object.__setattr__(self, "SONGS_DIR", self.MEDIA_DIR / "songs")
        object.__setattr__(self, "TEMPLATES_DIR", self.MEDIA_DIR / "templates")
        object.__setattr__(self, "CACHE_DIR", self.MEDIA_DIR / "cache")
        object.__setattr__(self, "AI_ASSETS_DIR", self.MEDIA_DIR / "cache" / "ai_visuals")
        return self

settings = Settings()

# Ensure directories exist
for d in [
    settings.DATA_DIR,
    settings.MEDIA_DIR,
    settings.UPLOADS_DIR,
    settings.REELS_DIR,
    settings.THUMBNAILS_DIR,
    settings.SONGS_DIR,
    settings.TEMPLATES_DIR,
    settings.CACHE_DIR,
    settings.AI_ASSETS_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
