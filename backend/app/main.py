import shutil
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api import reels, jobs, projects, assets

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="VidSnap AI 2026 Engine - Turn your ideas into polished short-form videos.",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

from app.services.creator_presets import CREATOR_PRESETS

@app.get("/api/presets")
async def get_presets():
    return [p.model_dump() for p in CREATOR_PRESETS.values()]

@app.get("/api/health")
async def health_check():
    ffmpeg_available = bool(shutil.which("ffmpeg"))
    ffprobe_available = bool(shutil.which("ffprobe"))
    elevenlabs_configured = bool(settings.ELEVENLABS_API_KEY)

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "ffmpeg": ffmpeg_available,
        "ffprobe": ffprobe_available,
        "elevenlabs_configured": elevenlabs_configured,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
