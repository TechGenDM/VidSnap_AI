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
