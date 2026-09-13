import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.models import JobStatus

client = TestClient(app)

def test_quick_reel_pipeline():
    img1 = settings.MEDIA_DIR / "templates" / "1.jpg"
    img2 = settings.MEDIA_DIR / "templates" / "2.jpg"

    assert img1.exists(), "Sample template image 1 must exist"
    assert img2.exists(), "Sample template image 2 must exist"

    # Send multipart upload
    with open(img1, "rb") as f1, open(img2, "rb") as f2:
        files = [
            ("images", ("slide_1.jpg", f1, "image/jpeg")),
            ("images", ("slide_2.jpg", f2, "image/jpeg")),
        ]
        data = {
            "script": "Welcome to VidSnap AI. Creating vertical videos has never been faster.",
            "voice": "adam",
            "music": "ambient_chill",
            "style": "cinematic",
        }
        response = client.post("/api/reels/quick", data=data, files=files)

    assert response.status_code == 200
    res_data = response.json()
    assert "project_id" in res_data
    assert "job_id" in res_data
    project_id = res_data["project_id"]
    job_id = res_data["job_id"]

