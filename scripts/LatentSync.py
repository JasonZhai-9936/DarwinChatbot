#latentsync
import os
import sys
import subprocess
import glob
import time
from pathlib import Path

# === Config ===
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  
LATENTSYNC_DIR = os.path.join(REPO_DIR, "LatentSync")                     
CONDA_ENV = "LatentSync"

INFERENCE_SCRIPT = os.path.join("scripts", "inference.py")                 
CONFIG_PATH = os.path.join(LATENTSYNC_DIR, "configs", "unet", "stage2.yaml")
CHECKPOINT_PATH = os.path.join(LATENTSYNC_DIR, "checkpoints", "latentsync_unet.pt")
STREAM_SPEECH_DIR = os.path.join(REPO_DIR, "stream", "speech")
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")
VIDEO_INPUT_PATH = os.path.join(REPO_DIR, "stream", "talking_chunks", "chunk4.mp4")

# === Utilities ===
def run(command, cwd=None, shell=False, fail_hard=False):
    """
    Runs a subprocess command.
    - shell: True if command is a string; False for list-style command
    - fail_hard: If True, raises error on failure; else logs and returns False
    Returns: True on success, False on failure
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
    # Give the file system a moment to catch up
    time.sleep(1)
    
    # First check
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        print(f"[VERIFY] File exists immediately: {filepath}")
        print(f"[VERIFY] File size: {file_size} bytes")
        return True
    else:
        print(f"[VERIFY] File does not exist immediately: {filepath}")
    
    # Wait and check again (sometimes files take time to appear due to caching/sync)
    print(f"[VERIFY] Waiting {wait_seconds} seconds to check again...")
    time.sleep(wait_seconds)
    
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        print(f"[VERIFY] File exists after waiting: {filepath}")
        print(f"[VERIFY] File size: {file_size} bytes")
        return True
    else:
        print(f"[VERIFY] File still does not exist after waiting: {filepath}")
        
        # Check if the directory exists
        dir_path = os.path.dirname(filepath)
        if os.path.exists(dir_path):
            print(f"[VERIFY] Directory exists: {dir_path}")
            print(f"[VERIFY] Directory contents: {os.listdir(dir_path)}")
        else:
            print(f"[VERIFY] Directory does not exist: {dir_path}")
        
        return False

# === Main Inference Function ===
def run_latentsync_inference():
    print("[LATENTSYNC] Starting lip sync process")
    
    # Get the latest audio file from the speech directory
    latest_audio = get_latest_audio(STREAM_SPEECH_DIR)
    if not latest_audio:
        print("[ERROR] No speech audio found in /stream/speech.")
        return False

    # Extract audio filename for the output video
    audio_filename = Path(latest_audio).stem
    output_path = os.path.join(STREAM_LIVE_DIR, f"final_{audio_filename}.mp4")
    
    # Full absolute path for debugging
    abs_output_path = os.path.abspath(output_path)
    print(f"[DEBUG] Full absolute output path: {abs_output_path}")

    # Ensure output directory exists
    os.makedirs(STREAM_LIVE_DIR, exist_ok=True)
    print(f"[DEBUG] Ensured output directory exists: {STREAM_LIVE_DIR}")
    print(f"[DEBUG] Directory contents before processing: {os.listdir(STREAM_LIVE_DIR)}")

    print(f"[DEBUG] Using LatentSync repo at: {LATENTSYNC_DIR}")
    print(f"[DEBUG] Using audio input: {latest_audio}")
    print(f"[DEBUG] Using video input: {VIDEO_INPUT_PATH}")
    print(f"[DEBUG] Output will be at: {output_path}")

    # Build the command to run LatentSync
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

    success = False
    try:
        success = run(command, cwd=LATENTSYNC_DIR)
        print(f"[LATENTSYNC] Command execution status: {'Success' if success else 'Failed'}")
        
        # Verify file was created
        file_exists = verify_file_exists(output_path)
        
        if file_exists:
            print(f"[SUCCESS] Output saved to {output_path}")
            print(f"[DEBUG] Directory contents after processing: {os.listdir(STREAM_LIVE_DIR)}")
            return True
        else:
            print(f"[ERROR] Output file was not created at {output_path}")
            return False
    except Exception as e:
        print(f"[ERROR] LatentSync failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("[INFO] Running LatentSync Inference directly...")
    success = run_latentsync_inference()
    if success:
        print("[INFO] LatentSync inference completed successfully.")
    else:
        print("[ERROR] LatentSync inference failed.")