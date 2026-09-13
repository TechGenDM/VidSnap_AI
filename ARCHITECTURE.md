# VidSnap AI Architecture & Design Philosophy

## Core Product Principle
> **“VidSnap edits the story, not the timeline.”**

Traditional video editors force creators onto multi-track timelines, demanding manual cuts, audio synchronization, keyframe motion, and padding adjustments. VidSnap abstracts away the timeline entirely. The user works with **sequential narrative scenes** (visual, narration, caption, duration), and the engine dynamically compiles the video.

---

## System Architecture Diagram

```mermaid
flowchart TB
    subgraph Client ["Frontend Tier (Next.js 15)"]
        UI_Home["/ (Landing Page + Phone Showcase)"]
        UI_Create["/create (Quick Reel & AI Reel Modes)"]
        UI_State["Render State Modal (Real-Time Checklist)"]
        UI_Projects["/projects (Workspace & Card Grid)"]
        UI_Story["/projects/[id] (Story-Based Scene Editor)"]
    end

    subgraph API ["Backend API Tier (FastAPI)"]
        Router["FastAPI App (app.main:app)"]
        ReelsAPI["/api/reels/quick & /ai"]
        JobsAPI["/api/jobs/{id} (State & SSE stream)"]
        ProjectsAPI["/api/projects & /projects/{id}/scenes"]
        AssetsAPI["/api/assets/music & /voices"]
    end

    subgraph CoreServices ["Core Video & AI Engine"]
        StorageService["Storage: Upload Validation & UUID Isolation"]
        TTSService["AI: ElevenLabs / Local Speech Engine"]
        AudioEngine["Audio: Duration Detection & Speech Ducking"]
        VideoEngine["FFmpeg 8.0: 9:16 Blurred Background & Captions"]
        JobManager["Job State Machine (Queued -> Completed)"]
    end

    subgraph StorageTier ["Data & Media Storage"]
        DB[(Thread-Safe Atomic JSON Store)]
        MediaUploads["media/uploads/{uuid}/"]
        MediaReels["media/reels/{uuid}.mp4"]
        MediaThumbs["media/thumbnails/{uuid}.jpg"]
        MediaSongs["media/songs/ (Royalty-Free Music)"]
    end

    UI_Create -->|Multipart Upload + Script| ReelsAPI
    ReelsAPI --> StorageService
    StorageService --> MediaUploads
    ReelsAPI --> JobManager
    JobManager --> DB

    JobManager -->|1. Generate Narration| TTSService
    JobManager -->|2. Measure Audio & Duck Music| AudioEngine
    AudioEngine --> MediaSongs
    JobManager -->|3. Compile 1080x1920 MP4| VideoEngine
    VideoEngine --> MediaReels
    VideoEngine --> MediaThumbs
    JobManager -->|Update State: Completed| DB

    UI_State -.->|Poll / SSE /api/jobs/{id}| JobsAPI
    JobsAPI -.-> DB

    UI_Projects --> ProjectsAPI
    UI_Story --> ProjectsAPI
    ProjectsAPI --> DB
```

---

## 1. Asynchronous Job State Machine

Jobs move through explicit, persisted states:

```
[queued] ──► [processing] ──► [generating_voice] ──► [generating_captions] ──► [rendering] ──► [completed]
     │              │                  │                       │                  │
     └──────────────┴──────────────────┴───────────────────────┴──────────────────┴────► [failed]
```

Every state change updates both the `Job` record and the `Project` record in the database. When a step fails, a structured error message is recorded without crashing the server.

---

## 2. Dynamic Audio-Visual Timing Engine

The legacy VidSnap 2025 prototype hardcoded a fixed 1-second duration per image:
```
# Legacy Bug:
file 'image1.jpg'
duration 1
file 'image2.jpg'
duration 1
```
This caused videos to terminate prematurely or fall out of sync with spoken narration.

In **VidSnap 2026**:
1. Voice narration is synthesized first.
2. `ffprobe` extracts exact narration length down to milliseconds:
   $$\text{total\_duration} = \text{audio\_duration}$$
3. Slide timing is dynamically assigned:
   $$\text{slide\_duration} = \frac{\text{total\_duration}}{\text{num\_images}}$$
4. Concat demuxing normalizes Sample Aspect Ratio with `setsar=1` so images of varying resolutions and aspect ratios composite seamlessly.

---

## 3. 9:16 Blurred Background Canvas

Instead of harsh black bars or distorted image stretching, the video engine uses an intelligent dual-stream filtergraph:
```
[0:v]split=2[v1][v2];
[v1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:5[bg];
[v2]scale=1080:1920:force_original_aspect_ratio=decrease[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,
drawtext=text='...':fontsize=42:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=18:x=(w-text_w)/2:y=h*0.78[vout]
```
This produces a cinematic vertical reel with blurred background depth and a crisp centered foreground.

---

## 4. Audio Ducking Architecture

When background music is selected:
- Speech is kept at 100% volume (`volume=1.0`).
- Background music is trimmed to the speech length, ducked to ~14% volume (`volume=0.14`), and given a 1.5-second smooth fade-out (`afade=t=out:st={duration-1.5}:d=1.5`).
- Streams are mixed with `amix=inputs=2:duration=first:dropout_transition=2`.
