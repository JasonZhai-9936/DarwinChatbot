# LivePortrait_pkl_generation.py


import os
import sys
import time
import subprocess
import shutil
from pathlib import Path

# === Config ===
ACCEPTED_VIDEO_EXTENSIONS = [".mp4"]
PKL_CATEGORIES = ["idle", "talking"]
CONDA_ENV = "LivePortrait"

# === Paths ===
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LivePortrait_DIR = os.path.join(REPO_DIR, "LivePortrait")
INFERENCE_SCRIPT = os.path.join(LivePortrait_DIR, "inference.py")
ASSETS_DIR = os.path.join(LivePortrait_DIR, "assets", "drivers")
INPUT_IMAGE = os.path.join(LivePortrait_DIR, "assets", "prompts", "Darwin4.png")

IDLE_VIDEO_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos")
PKL_ROOT_DIR = os.path.join(IDLE_VIDEO_DIR, "pkls")
IDLE_SOURCE_DIR = os.path.join(IDLE_VIDEO_DIR, "idle_videos")
TALKING_SOURCE_DIR = os.path.join(IDLE_VIDEO_DIR, "talking_videos")


def run(command, cwd=None):
    print(f"[RUN] {' '.join(command) if isinstance(command, list) else command}")
    try:
        subprocess.run(command, cwd=cwd, shell=isinstance(command, str), check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def ask_user_settings():
    print("=== PKL Batch Generator ===\n")
    while True:
        try:
            limit = int(input("How many videos do you want to process? (e.g. 5): "))
            break
        except ValueError:
            print("Please enter a valid number.")

    while True:
        category = input("Save .pkl files to which category? ('idle' or 'talking'): ").strip().lower()
        if category in PKL_CATEGORIES:
            break
        else:
            print("Invalid choice. Please enter 'idle' or 'talking'.")

    return limit, category

def generate_pkl_from_video(driving_path, dest_folder, timeout=150):
    driving_path = os.path.abspath(driving_path)
    driving_name = Path(driving_path).stem
    video_dir = os.path.dirname(driving_path)
    expected_pkl = os.path.join(video_dir, f"{driving_name}.pkl")

    print(f"\n[PROCESS] Starting inference for: {driving_path}")

    command = [
        "conda", "run", "-n", CONDA_ENV, "python", INFERENCE_SCRIPT,
        "-s", INPUT_IMAGE,
        "-d", driving_path,
        "-o", os.path.join(REPO_DIR, "outputs")
    ]

    process = subprocess.Popen(command)

    print(f"[WAIT] Watching for: {expected_pkl}")
    start_time = time.time()

    while True:
        if os.path.isfile(expected_pkl):
            print(f"[FOUND] {expected_pkl} created. Terminating process.")
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            break

        if time.time() - start_time > timeout:
            print(f"[TIMEOUT] No .pkl created in {timeout} sec for {driving_name}.")
            process.terminate()
            return False

        time.sleep(0.5)

    final_dest = os.path.join(dest_folder, f"{driving_name}.pkl")
    shutil.move(expected_pkl, final_dest)
    print(f"[DONE] Moved {expected_pkl} → {final_dest}")
    return True

def batch_generate_pkls(limit, category):
    category_dir = os.path.join(PKL_ROOT_DIR, category)
    source_dir = IDLE_SOURCE_DIR if category == "idle" else TALKING_SOURCE_DIR

    os.makedirs(category_dir, exist_ok=True)

    print(f"[INFO] Scanning: {source_dir}")

    existing_pkls = {
        os.path.splitext(f)[0]
        for f in os.listdir(category_dir)
        if f.endswith(".pkl")
    }

    all_videos = [
        os.path.join(source_dir, f)
        for f in os.listdir(source_dir)
        if os.path.splitext(f)[1].lower() in ACCEPTED_VIDEO_EXTENSIONS
    ]

    if not all_videos:
        print(f"[WARN] No supported video files found in {source_dir}.")
        return

    print(f"[INFO] Found {len(all_videos)} supported video(s).")
    print(f"[INFO] {len(existing_pkls)} already have .pkl files in '{category}' category.\n")

    processed = 0

    for video in all_videos:
        driving_name = Path(video).stem
        if driving_name in existing_pkls:
            print(f"[SKIP] {driving_name}.pkl already exists — skipping.")
            continue

        success = generate_pkl_from_video(video, category_dir)
        if success:
            processed += 1

        if processed >= limit:
            break

    # === Cleanup Outputs Directory ===
    print(f"\n[CLEANUP] Clearing all files in: {os.path.join(REPO_DIR, 'outputs')}")
    for file in os.listdir(os.path.join(REPO_DIR, "outputs")):
        file_path = os.path.join(REPO_DIR, "outputs", file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"[WARN] Could not delete {file_path}: {e}")
    print("[CLEANUP] Done.")

if __name__ == "__main__":
    limit, category = ask_user_settings()
    batch_generate_pkls(limit, category)
