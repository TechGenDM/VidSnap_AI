"""
End-to-End Acceptance Verification Script for Phase 2.5:
Creative Intelligence & Output Quality
Flow:
Idea -> Topic Interpretation -> Multi-Candidate Generation -> Quality Validation ->
Best Candidate -> Visual Matching -> Review -> Regeneration -> Scene Edit -> Render -> Final Video Inspection.
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.database import db
from app.models import JobStatus

client = TestClient(app)

def run_acceptance_verification():
    print("=" * 70)
    print("PHASE 2.5 CREATIVE INTELLIGENCE & OUTPUT QUALITY ACCEPTANCE TEST")
    print("=" * 70)

    prompt = "Explain why AI agents are changing software development."
    print(f"\n1. Submitting Idea: '{prompt}'")

    # Step 1: POST /api/reels/ai
    t0 = time.time()
    res = client.post(
        "/api/reels/ai",
        json={
            "prompt": prompt,
            "audience": "Tech Creators",
            "tone": "Educational",
            "length": "30s",
            "visual_style": "Minimal Tech",
            "voice": "adam",
            "music": "ambient_chill",
        },
    )
    assert res.status_code == 200, f"Failed AI Reel creation: {res.text}"
    plan_data = res.json()
    project_id = plan_data["project_id"]
    story = plan_data["story"]
    scenes = plan_data["scenes"]

    print(f"✓ Project Created: {project_id}")
    print(f"✓ Chosen Story Title: '{story['title']}'")
    print(f"✓ Hook Strategy: '{story.get('hook_strategy')}' | Score: {story.get('quality_score')}")
    print(f"✓ Hook: \"{story['hook']}\"")
    print("\nScenes Generated:")
    for s in story["scenes"]:
        print(f"  [{s.get('scene_role', 'scene').upper()}] Scene #{s['order']} (~{s['estimated_duration']}s):")
        print(f"    Narration: \"{s['narration']}\"")
        print(f"    Caption:   \"{s['caption']}\" ({len(s['caption'].split())} words)")
        print(f"    Visual:    \"{s['visual_direction']}\"")
        assert 2 <= len(s['caption'].split()) <= 7, f"Caption out of bounds: {s['caption']}"

    # Verify visual matching
    print("\nVisual Matching Assessment:")
    for idx, sc in enumerate(scenes):
        print(f"  Scene #{sc['order']}: {sc['visual_filename']} -> match_quality='{sc.get('match_quality')}'")
        if idx > 0:
            assert sc['visual_filename'] != scenes[idx - 1]['visual_filename'], "Consecutive duplicate visual detected!"

    # Step 2: Regenerate Story
    print("\n2. Testing Story Regeneration (Switching Creative Angle)...")
    regen_res = client.post(f"/api/projects/{project_id}/regenerate-story")
    assert regen_res.status_code == 200
    regen_story = regen_res.json()["story"]
    print(f"✓ Regenerated Hook Strategy: '{regen_story.get('hook_strategy')}'")
    print(f"✓ Regenerated Hook: \"{regen_story['hook']}\"")
    assert regen_story["hook"] != story["hook"], "Regenerated hook must differ from original hook!"

    # Step 3: Regenerate Single Scene
    print("\n3. Testing Context-Aware Scene 2 Regeneration...")
    scene2_res = client.post(
        f"/api/projects/{project_id}/scenes/2/regenerate",
        json={"feedback": "Make it focused on architecture"},
    )
    assert scene2_res.status_code == 200
    updated_scene2 = scene2_res.json()["scene"]
    print(f"✓ Regenerated Scene 2 [{updated_scene2.get('scene_role')}]:")
    print(f"    Narration: \"{updated_scene2['narration']}\"")
    print(f"    Caption:   \"{updated_scene2['caption']}\"")
    assert 2 <= len(updated_scene2['caption'].split()) <= 7

    # Step 4: Render Final Reel
    print("\n4. Triggering 1080x1920 Video Rendering...")
    render_res = client.post(f"/api/projects/{project_id}/render")
    assert render_res.status_code == 200
    job_id = render_res.json()["job_id"]
    print(f"✓ Render Job Enqueued: {job_id}")

    # Wait for render to complete
    max_wait = 90
    elapsed = 0
    final_project = None
    while elapsed < max_wait:
        time.sleep(2)
        elapsed += 2
        job = db.get_job(job_id)
        if not job:
            continue
        print(f"  [{job.status.value}] step='{job.step}' ({job.progress_percent}%)")
        if job.status == JobStatus.COMPLETED:
            final_project = db.get_project(project_id)
            break
        elif job.status == JobStatus.FAILED:
            raise RuntimeError(f"Rendering failed: {job.error_message}")

    assert final_project is not None, "Render timed out!"
    assert final_project.video_filename is not None, "No video filename on completed project!"

    video_path = Path(f"media/reels/{final_project.video_filename}")
    assert video_path.exists(), f"Rendered video does not exist at {video_path}"
    print(f"\n✓ Video Successfully Rendered: {video_path} ({video_path.stat().st_size:,} bytes)")

    # Step 5: ffprobe Video Inspection
    print("\n5. Deep Forensic FFprobe Stream Inspection...")
    ffprobe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,r_frame_rate,duration",
        "-of", "json",
        str(video_path),
    ]
    probe_out = subprocess.check_output(ffprobe_cmd).decode("utf-8")
    probe_v = json.loads(probe_out)
    v_stream = probe_v["streams"][0]

    ffprobe_a_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels",
        "-of", "json",
        str(video_path),
    ]
    probe_a_out = subprocess.check_output(ffprobe_a_cmd).decode("utf-8")
    probe_a = json.loads(probe_a_out)
    a_stream = probe_a["streams"][0]

    width = int(v_stream["width"])
    height = int(v_stream["height"])
    v_codec = v_stream["codec_name"]
    duration = float(v_stream["duration"])
    a_codec = a_stream["codec_name"]
    channels = int(a_stream["channels"])

    print(f"  Resolution:   {width}x{height} (Aspect Ratio 9:16 Vertical)")
    print(f"  Video Codec:  {v_codec}")
    print(f"  Audio Codec:  {a_codec} ({channels} channels, {a_stream['sample_rate']}Hz)")
    print(f"  Duration:     {duration:.2f} seconds")

    assert width == 1080 and height == 1920, f"Expected 1080x1920, got {width}x{height}"
    assert v_codec == "h264", f"Expected h264 video codec, got {v_codec}"
    assert a_codec == "aac", f"Expected aac audio codec, got {a_codec}"
    assert duration > 10.0, f"Expected duration > 10s, got {duration}"

    print("\n" + "=" * 70)
    print("PHASE 2.5 ACCEPTANCE VERIFICATION SUCCESSFUL!")
    print("=" * 70)

if __name__ == "__main__":
    run_acceptance_verification()
