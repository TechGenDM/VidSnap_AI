import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_failure_no_images():
    """Submitting without images must return 400 or 422 error."""
    data = {
        "script": "Testing without images.",
        "voice": "adam",
    }
    response = client.post("/api/reels/quick", data=data, files=[])
    assert response.status_code in [400, 422]
    assert "image" in response.text.lower() or "required" in response.text.lower()

def test_failure_invalid_file_extension():
    """Submitting a text file as an image must return 400 error."""
    fake_txt = io.BytesIO(b"This is not an image file.")
    files = [("images", ("document.txt", fake_txt, "text/plain"))]
    data = {
        "script": "Testing with invalid file extension.",
        "voice": "adam",
    }
    response = client.post("/api/reels/quick", data=data, files=files)
    assert response.status_code == 400
    assert "unsupported" in response.text.lower()

def test_failure_empty_script():
    """Submitting empty or whitespace-only script must fail."""
    img1 = settings.MEDIA_DIR / "templates" / "1.jpg"
    with open(img1, "rb") as f:
        files = [("images", ("test.jpg", f, "image/jpeg"))]
        data = {"script": "  ", "voice": "adam"}
        response = client.post("/api/reels/quick", data=data, files=files)
    assert response.status_code == 422

def test_failure_invalid_project_id():
    """Requesting non-existent project returns 404."""
    response = client.get("/api/projects/non-existent-uuid-12345")
    assert response.status_code == 404

def test_failure_invalid_job_id():
    """Requesting non-existent job returns 404."""
    response = client.get("/api/jobs/non-existent-job-12345")
    assert response.status_code == 404

def test_single_image_reel():
    """A Quick Reel with exactly 1 image must render successfully."""
    img1 = settings.MEDIA_DIR / "templates" / "1.jpg"
    with open(img1, "rb") as f:
        files = [("images", ("single_slide.jpg", f, "image/jpeg"))]
        data = {
            "script": "Single image quick reel test.",
            "voice": "rachel",
            "music": "ambient_chill",
        }
        response = client.post("/api/reels/quick", data=data, files=files)
    assert response.status_code == 200
    res = response.json()
    assert "project_id" in res
    assert "job_id" in res

def test_short_script_reel():
    """A very short script must render cleanly without duration errors."""
    img1 = settings.MEDIA_DIR / "templates" / "1.jpg"
    img2 = settings.MEDIA_DIR / "templates" / "2.jpg"
    with open(img1, "rb") as f1, open(img2, "rb") as f2:
        files = [
            ("images", ("img1.jpg", f1, "image/jpeg")),
            ("images", ("img2.jpg", f2, "image/jpeg")),
        ]
        data = {
            "script": "Hello world.",
            "voice": "josh",
            "music": "upbeat_pulse",
        }
        response = client.post("/api/reels/quick", data=data, files=files)
    assert response.status_code == 200

def test_failure_corrupted_image():
    """Uploading random corrupted bytes as an image must be rejected by Pillow verification."""
    corrupted_data = io.BytesIO(b"\xFF\xD8\xFF\xE0corrupted_non_image_payload_here")
    files = [("images", ("corrupt.jpg", corrupted_data, "image/jpeg"))]
    data = {
        "script": "Testing with corrupted image data.",
        "voice": "adam",
    }
    response = client.post("/api/reels/quick", data=data, files=files)
    assert response.status_code == 400
    assert "corrupted" in response.text.lower() or "not a valid image" in response.text.lower()

def test_failure_oversized_file():
    """Uploading a file exceeding 25MB limit must return HTTP 413."""
    # 26MB dummy buffer
    oversized_data = io.BytesIO(b"0" * (26 * 1024 * 1024))
    files = [("images", ("oversized.jpg", oversized_data, "image/jpeg"))]
    data = {
        "script": "Testing oversized file rejection.",
        "voice": "adam",
    }
    response = client.post("/api/reels/quick", data=data, files=files)
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.text.lower()

def test_story_edit_and_rerender_flow():
    """Verifies the complete story editing and re-rendering flow."""
    # 1. Create Quick Reel
    img1 = settings.MEDIA_DIR / "templates" / "1.jpg"
    with open(img1, "rb") as f:
        files = [("images", ("slide1.jpg", f, "image/jpeg"))]
        data = {
            "script": "Initial story narration.",
            "voice": "adam",
            "music": "none",
        }
        create_res = client.post("/api/reels/quick", data=data, files=files)
    assert create_res.status_code == 200
    project_id = create_res.json()["project_id"]

    # 2. Fetch project
    proj_res = client.get(f"/api/projects/{project_id}")
    assert proj_res.status_code == 200
    project = proj_res.json()
    assert len(project["scenes"]) > 0
    scene_id = project["scenes"][0]["id"]

    # 3. Edit story scene text
    update_res = client.put(
        f"/api/projects/{project_id}/scenes",
        json={
            "scenes": [
                {
                    "id": scene_id,
                    "narration": "Updated refined narration after editing.",
                    "caption": "Updated caption.",
                }
            ]
        },
    )
    assert update_res.status_code == 200
    updated_proj = update_res.json()
    assert "Updated refined narration" in updated_proj["script"]

    # 4. Trigger re-render
    render_res = client.post(f"/api/projects/{project_id}/render")
    assert render_res.status_code == 200
    assert "job_id" in render_res.json()

    # 5. Delete project cleanup
    del_res = client.delete(f"/api/projects/{project_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/projects/{project_id}").status_code == 404

