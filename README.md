# VidSnap AI (2026 Edition)

> **“Turn your ideas into videos.”**
> *VidSnap edits the story, not the timeline.*

VidSnap AI is an AI-powered short-form video creation engine. It enables creators, educators, and founders to transform raw photos, scripts, and high-level ideas into polished, vertical (9:16) video reels with AI narration, kinetic captions, subtle motion, and background music — without manual timeline editing.

---

## 🌟 Key Features

* **Quick Reel (Implemented)**: Drop in 1 to 15 photos, write your script, pick a voice and soundtrack, and get a complete 1080×1920 Reel in seconds.
* **AI Reel (Story Planner Implemented)**: Enter a topic or prompt. The AI structures high-retention hooks, audience-targeted narration, and scene breakdowns.
* **Dynamic Speech Synchronization**: Slide duration is automatically derived from the actual narration length (`audio_duration / num_slides`), eliminating the fixed 1-second slide limit of legacy tools.
* **9:16 Blurred Background Framing**: Intelligent filtergraph scales and blurs images to fill the vertical canvas, framing the crisp original in the center without ugly black bars.
* **Speech/Music Auto-Ducking**: Background music is dynamically mixed at -17dB beneath the narration and smoothly fades out as speech concludes.
* **Kinetic Captions**: Generates clean, high-contrast captions burned into the lower third of each scene.
* **Story-Based Editor (`/projects/[id]`)**: Edit the story scene-by-scene (narration, caption, visuals) with live vertical phone preview and an "Ask VidSnap" conversational assistant.
* **Robust Job State Tracking**: Real-time progress updates (`queued` → `processing` → `generating_voice` → `generating_captions` → `rendering` → `completed`).

---

## 🏗️ Architecture & Tech Stack

* **Frontend**: Next.js 15 (App Router, TypeScript, Tailwind CSS, Lucide icons, dark-first Linear/Vercel design system).
* **Backend**: FastAPI (Python 3.12/3.14) with Pydantic validation, modular AI providers, and background worker pipeline.
* **Video Engine**: FFmpeg 8.0.1 running safe, injection-proof subprocess pipelines (`shell=False`).
* **TTS Audio Engine**: ElevenLabs API with graceful fallback to local high-quality system speech synthesis.
* **Persistence**: Lightweight, atomic file-backed JSON/SQLite database with thread-safe locking.

---

## 🚀 Quick Start

### 1. Prerequisites
* **Python**: 3.12 or 3.14
* **Node.js**: v20+ (v25 supported)
* **FFmpeg & FFprobe**: Installed and available in your `PATH` (e.g., `brew install ffmpeg`)

### 2. Backend Setup
```bash
# From repository root
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run backend on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# In another terminal, from repository root
cd frontend
npm install
npm run dev -- -p 3000
```
Open **`http://localhost:3000`** in your browser.

---

## 🔑 Environment Variables

Create or update `.env` in the project root:

```env
# Optional: ElevenLabs Voice API Key
# If omitted or invalid, VidSnap seamlessly falls back to high-quality local speech synthesis
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

---

## 🧪 Testing

Run backend test suite:
```bash
PYTHONPATH=backend backend/venv/bin/pytest backend/tests/
```

Test production frontend build:
```bash
cd frontend && npm run build
```

---

## 📂 Project Structure

```
VidSnap_AI/
├── backend/
│   ├── app/
│   │   ├── api/             # API routes (reels, jobs, projects, assets)
│   │   ├── services/        # Storage, AI/TTS, Audio, Video, Jobs
│   │   ├── config.py        # Settings & paths
│   │   ├── database.py      # Persistence layer
│   │   ├── models.py        # Data models
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── main.py          # FastAPI app & CORS
│   ├── tests/               # Pytest suite
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/      # Navbar, Footer
│   │   ├── create/          # Reel creation interface & status
│   │   ├── projects/        # Workspace & [id] Story Editor
│   │   ├── templates/       # Template gallery placeholder
│   │   ├── settings/        # Settings & integrations
│   │   ├── globals.css      # Dark-first design system
│   │   └── page.tsx         # Modern homepage & phone showcase
│   ├── package.json
│   └── next.config.ts       # Backend proxy rewrites
├── media/                   # Rendered reels, thumbnails, uploads, songs
├── legacy/                  # Archived 2025 prototype files
├── ARCHITECTURE.md
├── API.md
└── DEVELOPMENT.md
```
