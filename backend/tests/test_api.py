import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["ffmpeg"] is True
    assert data["ffprobe"] is True

def test_assets_endpoints():
    music_resp = client.get("/api/assets/music")
    assert music_resp.status_code == 200
    assert len(music_resp.json()) >= 3

    voices_resp = client.get("/api/assets/voices")
    assert voices_resp.status_code == 200
    assert len(voices_resp.json()) >= 4

def test_projects_list():
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
