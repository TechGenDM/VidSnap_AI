from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from a .env file (if present)
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
	raise RuntimeError(
		"ELEVENLABS_API_KEY is not set. Create a .env file from .env.example and set ELEVENLABS_API_KEY."
	)