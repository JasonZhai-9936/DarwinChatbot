#latentsync
import os
import sys
import subprocess
import glob
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
    audio_files = sorted(
        glob.glob(os.path.join(directory, "speech*")),
        key=os.path.getctime,
        reverse=True    
    )
    return audio_files[0] if audio_files else None

# === Main Inference Function ===
def run_latentsync_inference():
    print("Latentsync call started")
    latest_audio = get_latest_audio(STREAM_SPEECH_DIR)
    if not latest_audio:
        print("[ERROR] No speech audio found in /stream/speech.")
        return False

    audio_filename = Path(latest_audio).stem
    output_path = os.path.join(STREAM_LIVE_DIR, f"final_{audio_filename}.mp4")

    os.makedirs(STREAM_LIVE_DIR, exist_ok=True)

    print(f"[DEBUG] Using LatentSync repo at: {LATENTSYNC_DIR}")
    print(f"[DEBUG] Inference script relative path: {INFERENCE_SCRIPT}")

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

    try:
        run(command, cwd=LATENTSYNC_DIR) 
        print(f"[SUCCESS] Output saved to {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] LatentSync failed: {e}")
        return False

if __name__ == "__main__":
    print("[INFO] Running LatentSync Inference directly...")
    success = run_latentsync_inference()
    if success:
        print("[INFO] LatentSync inference completed successfully.")
    else:
        print("[ERROR] LatentSync inference failed.")
