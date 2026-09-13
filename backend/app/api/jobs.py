import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.database import db
from app.models import JobStatus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    Returns current status and progress of a rendering job.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    project = db.get_project(job.project_id)
    video_url = project.video_url if project else None

    return {
        **job.model_dump(),
        "video_url": video_url,
    }

@router.get("/{job_id}/stream")
async def stream_job_status(job_id: str):
    """
    Server-Sent Events (SSE) endpoint providing real-time rendering state updates.
    """
    async def event_generator():
        while True:
            job = db.get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            project = db.get_project(job.project_id)
            video_url = project.video_url if project else None

            payload = {
                **job.model_dump(),
                "video_url": video_url,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
