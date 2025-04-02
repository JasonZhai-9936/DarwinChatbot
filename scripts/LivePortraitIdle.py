# LivePortraitMain.py

import subprocess
import os
import sys
import random
import glob
import shutil
import time

# === Config ===
CONTROLLER_POLLING_INTERVAL = 4
CONDA_ENV = "LivePortrait"

# === Paths ===
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LivePortrait_DIR = os.path.join(REPO_DIR, "LivePortrait")
INFERENCE_SCRIPT = os.path.join(LivePortrait_DIR, "inference.py")
ASSETS_DIR = os.path.join(LivePortrait_DIR, "assets", "drivers")
OUTPUT_DIR = os.path.join(REPO_DIR, "outputs")
INPUT_IMAGE = os.path.join(LivePortrait_DIR, "assets", "prompts", "Darwin4.png")
LAST_FRAME_IMAGE = os.path.join(OUTPUT_DIR, "last_frame.png")

# === Animations ===
priority_animations = ["d5.pkl", "d1.pkl", "d2.pkl"]
animations = [
    "d0.mp4", "d0.pkl", "d1.pkl", "d10.mp4", "d10.pkl",
    "d11.mp4", "d12.mp4", "d12.pkl", "d13.mp4", "d14.mp4",
    "d18.mp4", "d18.pkl", "d19.mp4", "d19.pkl", "d2.pkl",
    "d20.mp4", "d3.mp4", "d5.pkl", "d6.mp4",
    "d7.pkl", "d8.pkl", "d9.mp4"
]

def run(command, cwd=None):
    print(f"[RUN] {' '.join(command) if isinstance(command, list) else command}")
    try:
        subprocess.run(command, cwd=cwd, shell=isinstance(command, str), check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def get_latest_output(directory):
    video_files = glob.glob(os.path.join(directory, "*.mp4"))
    if not video_files:
        print(f"[ERROR] No MP4 files found in {directory}")
        sys.exit(1)
    return max(video_files, key=os.path.getctime)

def extract_last_frame(video_path, output_image_path):
    print(f"[INFO] Extracting last frame from {video_path} to {output_image_path}")
    command = f"ffmpeg -y -sseof -3 -i \"{video_path}\" -vframes 1 \"{output_image_path}\""
    run(command)

def start_generation_loop(get_is_on, infinite_generation=False, num_chunks=5, start_index=1):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    used_priority_animations = set()
    current_input_image = INPUT_IMAGE
    chunk_index = start_index
    generated_chunks = []
    max_chunks = float('inf') if infinite_generation else num_chunks

    print("[INFO] Starting controlled generation loop...")

    while chunk_index < start_index + max_chunks:
        if get_is_on():
            print(f"\n[STEP] Generating chunk {chunk_index}")

            # Choose driver
            if len(used_priority_animations) < len(priority_animations):
                available_priority = list(set(priority_animations) - used_priority_animations)
                driving_video = random.choice(available_priority)
                used_priority_animations.add(driving_video)
            else:
                driving_video = random.choice(animations)

            driving_video_path = os.path.join(ASSETS_DIR, driving_video)

            # Call inference
            run([
                "conda", "run", "-n", CONDA_ENV, "python", INFERENCE_SCRIPT,
                "-s", current_input_image,
                "-d", driving_video_path,
                "-o", OUTPUT_DIR
            ])

            # Derive output filename
            driving_name = os.path.splitext(os.path.basename(driving_video))[0]
            input_name = os.path.splitext(os.path.basename(current_input_image))[0]
            output_filename = f"{input_name}--{driving_name}.mp4"
            output_chunk_path = os.path.join(OUTPUT_DIR, output_filename)

            if not os.path.isfile(output_chunk_path):
                print(f"[ERROR] Expected output file not found: {output_chunk_path}")
                sys.exit(1)

            print(f"[INFO] Saved chunk as {output_chunk_path}")

            # Extract last frame
            extract_last_frame(output_chunk_path, LAST_FRAME_IMAGE)
            current_input_image = LAST_FRAME_IMAGE

            # Track chunk
            generated_chunks.append(output_chunk_path)
            chunk_index += 1
        else:
            print("[WAITING] isOn is False. Waiting to generate...")
            time.sleep(CONTROLLER_POLLING_INTERVAL)

    # === Merge all chunks ===
    if generated_chunks:
        print("\n[INFO] Merging all generated chunks into final_output.mp4...")

        merge_list_path = os.path.join(OUTPUT_DIR, "merge_list.txt")
        with open(merge_list_path, "w") as f:
            for chunk_path in generated_chunks:
                rel_path = os.path.relpath(chunk_path, OUTPUT_DIR)
                f.write(f"file '{rel_path}'\n")

        final_output_path = os.path.join(OUTPUT_DIR, "final_output.mp4")

        merge_cmd = (
            f"ffmpeg -y -f concat -safe 0 -i \"{merge_list_path}\" "
            f"-c:v copy -c:a aac -strict experimental \"{final_output_path}\""
        )

        run(merge_cmd)

        if os.path.isfile(final_output_path):
            print(f"[SUCCESS] Final merged video saved to {final_output_path}")
        else:
            print("[ERROR] Final merged video not created.")
    else:
        print("[WARN] No chunks were generated, skipping merge.")

    # Optional cleanup
    # for path in generated_chunks:
    #     os.remove(path)
    # print("[INFO] Cleaned up individual chunk files.")

if __name__ == "__main__":
    print(f"[INFO] This script is meant to be called externally")
