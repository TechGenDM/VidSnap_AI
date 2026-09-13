# VidSnap AI Developer Guide

## Local Environment Setup

### 1. Requirements
* macOS or Linux
* Python 3.12 (preferred) or 3.14
* Node.js v20+ & npm v10+
* FFmpeg 8.x with `libx264` and `aac` support

---

## 2. Running the Full Stack

### Terminal 1: FastAPI Backend
```bash
# Activate venv
cd backend
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: Next.js Frontend
```bash
cd frontend
npm install
npm run dev -- -p 3000
```

Access the application at `http://localhost:3000`.

---

## 3. Running Automated Tests

### Backend Unit & Integration Tests
```bash
PYTHONPATH=backend backend/venv/bin/pytest backend/tests/ -v
```

The test suite validates:
* Service health and tool discovery (`ffmpeg`, `ffprobe`)
* Assets catalogs (voices and music)
* Project creation, retrieval, and deletion
* End-to-end Quick Reel video rendering pipeline with blurred background framing, audio ducking, and caption overlay.

### Frontend Production Build Test
```bash
cd frontend
npm run build
```
Validates TypeScript types, Turbopack compilation, and static page prerendering across all routes.
