# VidSnap AI REST API Reference

Base URL: `http://127.0.0.1:8000` (proxied via Next.js `/api/*`)

---

## 1. System Health

### `GET /api/health`
Returns service availability, FFmpeg status, and ElevenLabs API key configuration.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "app": "VidSnap AI",
  "version": "2.0.0",
  "ffmpeg": true,
  "ffprobe": true,
  "elevenlabs_configured": true
}
```

---

## 2. Reels & Video Creation

### `POST /api/reels/quick`
Creates a Quick Reel from uploaded images and script.

**Request**: `multipart/form-data`
* `script` (string, required): Narration text (3–5000 chars).
* `voice` (string, optional): `"adam"` | `"rachel"` | `"josh"` | `"antoni"`.
* `music` (string, optional): `"ambient_chill"` | `"upbeat_pulse"` | `"lofi_beat"` | `"none"`.
* `style` (string, optional): `"cinematic"` | `"dynamic"` | `"minimal"`.
* `images` (files, required): 1 to 15 image files (`.jpg`, `.jpeg`, `.png`, `.webp`).
* `image_order` (string, optional): JSON array of image reordering indices.

**Response (200 OK)**:
```json
{
  "project_id": "76de2e28-7af3-4cef-af28-b0cef9ea0fdd",
  "job_id": "8de29a47-df82-48b3-a1ad-7f99190f36a1",
  "status": "queued",
  "message": "Quick Reel job enqueued successfully."
}
```

### `POST /api/reels/ai`
Plans an AI Reel from an idea prompt and audience parameters.

**Request (JSON)**:
```json
{
  "prompt": "Explain why AI agents are changing software development in 2026",
  "audience": "Tech Creators",
  "tone": "Thought-Provoking",
  "length": "30s",
  "visual_style": "Cinematic Photography",
  "voice": "adam"
}
```

---

## 3. Jobs & Rendering Status

### `GET /api/jobs/{job_id}`
Returns the current rendering state and percentage progress.

**Response (200 OK)**:
```json
{
  "id": "8de29a47-df82-48b3-a1ad-7f99190f36a1",
  "project_id": "76de2e28-7af3-4cef-af28-b0cef9ea0fdd",
  "status": "completed",
  "step": "Your Reel is ready 🎉",
  "progress_percent": 100,
  "video_url": "/media/reels/76de2e28-7af3-4cef-af28-b0cef9ea0fdd.mp4",
  "error_message": null,
  "created_at": "2026-09-13T13:02:12.123456+00:00",
  "updated_at": "2026-09-13T13:02:18.123456+00:00"
}
```

### `GET /api/jobs/{job_id}/stream`
Server-Sent Events (SSE) stream pushing job progress updates every 500ms until completion.

---

## 4. Projects & Story Scenes

### `GET /api/projects`
Lists all creator projects sorted by creation date descending.

### `GET /api/projects/{project_id}`
Returns project details, duration, video URL, thumbnail, and scene list.

### `DELETE /api/projects/{project_id}`
Deletes the project, its rendered video, and thumbnail files.

### `PUT /api/projects/{project_id}/scenes`
Updates narration and screen captions for individual scenes without touching a timeline.

**Request (JSON)**:
```json
{
  "scenes": [
    {
      "id": "scene_1",
      "narration": "Updated narration text",
      "caption": "Updated caption on screen"
    }
  ]
}
```

### `POST /api/projects/{project_id}/assistant`
Executes natural language commands via the "Ask VidSnap" assistant.

**Request (JSON)**:
```json
{
  "command": "Make the intro more attention-grabbing"
}
```

---

## 5. Assets & Catalog

### `GET /api/assets/music`
Returns available royalty-free background music tracks with preview identifiers.

### `GET /api/assets/voices`
Returns available AI narrator voices with gender, accent, and descriptions.
