import os
import sys
import subprocess
import glob
from pathlib import Path

# === Config ===
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # your repo root
LATENTSYNC_DIR = os.path.join(REPO_DIR, "LatentSync")                      # external repo root
CONDA_ENV = "LatentSync"

INFERENCE_SCRIPT = os.path.join("scripts", "inference.py")                 # relative to LATENTSYNC_DIR
CONFIG_PATH = os.path.join(LATENTSYNC_DIR, "configs", "unet", "stage2.yaml")
CHECKPOINT_PATH = os.path.join(LATENTSYNC_DIR, "checkpoints", "latentsync_unet.pt")
STREAM_SPEECH_DIR = os.path.join(REPO_DIR, "stream", "speech")
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")
VIDEO_INPUT_PATH = os.path.join(REPO_DIR, "stream", "talking_chunks", "chunk4.mp4")

# === Utilities ===
def run(command, cwd=None):
    print(f"[RUN] {' '.join(command) if isinstance(command, list) else command}")
    subprocess.run(command, cwd=cwd, shell=isinstance(command, str), check=True)

def get_latest_audio(directory):
    audio_files = sorted(
        glob.glob(os.path.join(directory, "speech*")),
        key=os.path.getctime,
        reverse=True
    )
    return audio_files[0] if audio_files else None

# === Main Inference Function ===
def run_latentsync_inference():
    latest_audio = get_latest_audio(STREAM_SPEECH_DIR)
    if not latest_audio:
        print("[ERROR] No speech audio found in /stream/speech.")
        return False

    audio_filename = Path(latest_audio).stem
    output_path = os.path.join(STREAM_LIVE_DIR, f"{audio_filename}_lipsync.mp4")

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
        run(command, cwd=LATENTSYNC_DIR)  # run from LatentSync root
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
