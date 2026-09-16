import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings, PROJECT_ROOT
from app.api import reels, jobs, projects, assets
from app.services.creator_presets import CREATOR_PRESETS

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="VidSnap AI 2026 Engine - Turn your ideas into polished short-form videos.",
    debug=settings.DEBUG,
)

# Seed default media assets if mounted volume is new / empty
def _seed_default_media():
    default_templates = Path("/app/default_media/templates")
    default_songs = Path("/app/default_media/songs")
    
    src_templates = default_templates if default_templates.exists() else (PROJECT_ROOT / "media" / "templates")
    src_songs = default_songs if default_songs.exists() else (PROJECT_ROOT / "media" / "songs")
    
    if src_templates.exists():
        settings.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        for t_file in src_templates.glob("*.*"):
            dest = settings.TEMPLATES_DIR / t_file.name
            if not dest.exists() and t_file.resolve() != dest.resolve():
                shutil.copy2(t_file, dest)

    if src_songs.exists():
        settings.SONGS_DIR.mkdir(parents=True, exist_ok=True)
        for s_file in src_songs.glob("*.*"):
            dest = settings.SONGS_DIR / s_file.name
            if not dest.exists() and s_file.resolve() != dest.resolve():
                shutil.copy2(s_file, dest)

_seed_default_media()

# Enable CORS for Next.js frontend with production origin allowlist
cors_origins = settings.CORS_ORIGINS
allow_creds = True
if "*" in cors_origins:
    allow_creds = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media directory for video streaming, thumbnails, and uploads
app.mount("/media", StaticFiles(directory=str(settings.MEDIA_DIR)), name="media")

# Include Routers
app.include_router(reels.router)
app.include_router(jobs.router)
app.include_router(projects.router)
app.include_router(assets.router)

@app.get("/api/presets")
async def get_presets():
    return [p.model_dump() for p in CREATOR_PRESETS.values()]

@app.get("/api/health")
async def health_check():
    ffmpeg_available = bool(shutil.which("ffmpeg"))
    ffprobe_available = bool(shutil.which("ffprobe"))
    elevenlabs_configured = bool(settings.ELEVENLABS_API_KEY)

    # Verify storage directory writeability
    storage_writable = False
    try:
        test_file = settings.DATA_DIR / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        storage_writable = True
    except Exception:
        storage_writable = False

    is_healthy = ffmpeg_available and ffprobe_available and storage_writable

    return {
        "status": "healthy" if is_healthy else "degraded",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "ffmpeg": ffmpeg_available,
        "ffprobe": ffprobe_available,
        "storage_writable": storage_writable,
        "elevenlabs_configured": elevenlabs_configured,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "debug_mode": settings.DEBUG,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
