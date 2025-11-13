# VidSnap_AI

Small Flask app and processing scripts to convert uploaded images + description into a short vertical "reel" video using ffmpeg and ElevenLabs text-to-speech.

Quick start

1. Create a virtual environment and activate it (zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example and add your ElevenLabs API key:

```bash
cp .env.example .env
# then open .env and replace the placeholder with your real key
```

4. Run the Flask app (development mode):

```bash
python main.py
```

5. Run the background processor that creates reels (in another terminal):

```bash
python generate_process.py
```

Notes
- Put uploads under `user_uploads/<uuid>/` (the web UI does this when you POST files via `/create`).
- ffmpeg is required on your machine and must be available in PATH for `generate_process.py` to create reels.
- Keep your `.env` secret; do not commit it.

Troubleshooting
- If Python raises an exception about `ELEVENLABS_API_KEY` missing, ensure `.env` exists and contains `ELEVENLABS_API_KEY`.
- If ffmpeg subprocesses fail, run the `ffmpeg` command printed in the script manually to see more details.
