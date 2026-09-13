from fastapi import APIRouter
from app.services.audio import get_available_music
from app.services.ai import get_available_voices

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("/music")
async def list_music_tracks():
    """
    Returns available royalty-free background music tracks.
    """
    return get_available_music()

@router.get("/voices")
async def list_voices():
    """
    Returns available AI narrator voices.
    """
    return get_available_voices()
