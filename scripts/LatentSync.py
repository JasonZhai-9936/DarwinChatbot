import os
import sys
import subprocess
import glob
import time
import random
from pathlib import Path

# === Config ===
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LATENTSYNC_DIR = os.path.join(REPO_DIR, "LatentSync")
CONDA_ENV = "LatentSync"

# Directory containing img2vid-generated chunks
VIDEO_CHUNKS_DIR = os.path.join(REPO_DIR, "stream", "chunks", "img2vid_chunks")

# Function to pick a random .mp4 video from a directory

def get_random_video(directory):
    videos = glob.glob(os.path.join(directory, "*.mp4"))
    if not videos:
        return None
    return random.choice(videos)

# Pick a random video as input
VIDEO_INPUT_PATH = get_random_video(VIDEO_CHUNKS_DIR)

# Paths for inference
INFERENCE_SCRIPT = os.path.join("scripts", "inference.py")
CONFIG_PATH = os.path.join(LATENTSYNC_DIR, "configs", "unet", "stage2.yaml")
CHECKPOINT_PATH = os.path.join(LATENTSYNC_DIR, "checkpoints", "latentsync_unet.pt")
STREAM_SPEECH_DIR = os.path.join(REPO_DIR, "stream", "speech")
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")

# === Utilities ===
def run(command, cwd=None, shell=False, fail_hard=False):
    """
    Runs a subprocess command.
    """
    cmd_str = command if isinstance(command, str) else ' '.join(command)
    print(f"[RUN] {cmd_str}")
    try:
        subprocess.run(command, cwd=cwd, shell=shell or isinstance(command, str), check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}")
        if fail_hard:
            raise
        return False


def get_latest_audio(directory):
    """Find the most recent audio file in the directory."""
    audio_files = sorted(
        glob.glob(os.path.join(directory, "speech*.wav")),
        key=os.path.getctime,
        reverse=True
    )
    return audio_files[0] if audio_files else None


def verify_file_exists(filepath, wait_seconds=5):
    """Verify that a file exists and report its details."""
    time.sleep(1)
    if os.path.exists(filepath):
        print(f"[VERIFY] File exists immediately: {filepath} (size={os.path.getsize(filepath)} bytes)")
        return True
    print(f"[VERIFY] File not found immediately: {filepath}")
    print(f"[VERIFY] Waiting {wait_seconds}s to retry...")
    time.sleep(wait_seconds)
    if os.path.exists(filepath):
        print(f"[VERIFY] File exists after waiting: {filepath} (size={os.path.getsize(filepath)} bytes)")
        return True
    # Directory debug
    dir_path = os.path.dirname(filepath)
    if os.path.exists(dir_path):
        print(f"[VERIFY] Directory exists: {dir_path}")
        print(f"[VERIFY] Contents: {os.listdir(dir_path)}")
    else:
        print(f"[VERIFY] Directory missing: {dir_path}")
    return False


def run_latentsync_inference():
    print("[LATENTSYNC] Starting lip sync process")

    # Check video input
    if not VIDEO_INPUT_PATH:
        print(f"[ERROR] No .mp4 videos found in {VIDEO_CHUNKS_DIR}")
        return False
    print(f"[DEBUG] Selected random video: {VIDEO_INPUT_PATH}")

    # Get latest audio
    latest_audio = get_latest_audio(STREAM_SPEECH_DIR)
    if not latest_audio:
        print(f"[ERROR] No speech audio found in {STREAM_SPEECH_DIR}.")
        return False

    audio_filename = Path(latest_audio).stem
    output_path = os.path.join(STREAM_LIVE_DIR, f"final_{audio_filename}.mp4")

    # Ensure output directory exists
    os.makedirs(STREAM_LIVE_DIR, exist_ok=True)

    print(f"[DEBUG] Using LatentSync repo at: {LATENTSYNC_DIR}")
    print(f"[DEBUG] Audio input: {latest_audio}")
    print(f"[DEBUG] Output will be at: {output_path}")

    command = [
        "conda", "run", "-n", CONDA_ENV, "python", "-m", "scripts.inference",
        "--unet_config_path", CONFIG_PATH,
        "--inference_ckpt_path", CHECKPOINT_PATH,
        "--inference_steps", "20",
        "--guidance_scale", "1.5",
        "--video_path", VIDEO_INPUT_PATH,
        "--audio_path", latest_audio,
        "--video_out_path", output_path
    ]

    success = run(command, cwd=LATENTSYNC_DIR)
    print(f"[LATENTSYNC] Command execution status: {'Success' if success else 'Failed'}")

    if not success:
        return False

    if verify_file_exists(output_path):
        print(f"[SUCCESS] Output saved to {output_path}")
        return True
    print(f"[ERROR] Output file was not created at {output_path}")
    return False


if __name__ == "__main__":
    print("[INFO] Running LatentSync Inference directly...")
    if run_latentsync_inference():
        print("[INFO] LatentSync inference completed successfully.")
    else:
        print("[ERROR] LatentSync inference failed.")
