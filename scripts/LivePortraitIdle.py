# LivePortraitIdle.py

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
#some of these are unused by new funcs
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LivePortrait_DIR = os.path.join(REPO_DIR, "LivePortrait")
INFERENCE_SCRIPT = os.path.join(LivePortrait_DIR, "inference.py")
ASSETS_DIR = os.path.join(LivePortrait_DIR, "assets", "drivers")
OUTPUT_DIR = os.path.join(REPO_DIR, "temp_outputs")
STREAM_OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "idle_chunks")
STREAM_ASSETS_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos\pkls\idle")
INPUT_IMAGE = os.path.join(LivePortrait_DIR, "assets", "prompts", "darwin_young.png")
LAST_FRAME_IMAGE = os.path.join(OUTPUT_DIR, "last_frame.png")


#paths used by final streaming funcs
STREAM_OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "idle_chunks")
STREAM_IDLE_ASSETS_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos\pkls\idle")
STREAM_TALKING_ASSETS_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos\pkls\talking")
STREAM_IDLE_OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "idle_chunks")
STREAM_TALKING_OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "idle_chunks")

# === Animations ===
priority_animations = ["bbal8p.pkl","bbal6n.pkl","bbal7s.pkl"]
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
    
    
def generate_fixed_chunks(get_is_on, mode, chunks_per_video=3, start_video_index=1, video_limit=None):
    assert mode in ["idle", "talking"], "Mode must be either 'idle' or 'talking'"

    # === Select paths based on mode ===
    if mode == "idle":
        STREAM_OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "idle_chunks")
        ASSETS_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos", "pkls", "idle")
    else:
        STREAM_OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "talking_chunks")
        ASSETS_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos", "pkls", "talking")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(STREAM_OUTPUT_DIR, exist_ok=True)

    # === Load all .pkl drivers ===
    all_drivers = [
        f for f in os.listdir(ASSETS_DIR)
        if f.endswith(".pkl")
    ]

    if not all_drivers:
        print(f"[ERROR] No driver .pkl files found in {ASSETS_DIR}")
        return

    used_drivers = set()

    # === Determine starting chunk index based on existing files ===
    existing_chunks = [
        f for f in os.listdir(STREAM_OUTPUT_DIR)
        if f.startswith("chunk") and f.endswith(".mp4")
    ]

    existing_numbers = []
    for name in existing_chunks:
        try:
            number = int(name[len("chunk"):-len(".mp4")])
            existing_numbers.append(number)
        except ValueError:
            continue

    video_index = max(existing_numbers, default=start_video_index - 1) + 1
    print(f"[INFO] Starting from chunk number {video_index}")

    print("[INFO] Starting infinite grouped chunk generation (or until video_limit)...")

    while video_limit is None or video_index < start_video_index + video_limit:
        if not get_is_on():
            print("[WAITING] isOn is False. Waiting to generate...")
            time.sleep(CONTROLLER_POLLING_INTERVAL)
            return

        print(f"\n[INFO] Starting video #{video_index} (will generate {chunks_per_video} chunks)")

        chunk_index = 1
        generated_chunks = []
        current_input_image = INPUT_IMAGE  # Reset to global INPUT_IMAGE each batch

        while chunk_index <= chunks_per_video:
            print(f"[STEP] Generating chunk {chunk_index}/{chunks_per_video} for video {video_index}")

            # Pick a unique driver if available
            available_drivers = list(set(all_drivers) - used_drivers)
            if not available_drivers:
                used_drivers.clear()
                available_drivers = all_drivers

            driving_video = random.choice(available_drivers)
            used_drivers.add(driving_video)

            driving_video_path = os.path.join(ASSETS_DIR, driving_video)

            # Call inference
            run([
                "conda", "run", "-n", CONDA_ENV, "python", INFERENCE_SCRIPT,
                "-s", current_input_image,
                "-d", driving_video_path,
                "-o", OUTPUT_DIR
            ])

            # Determine output filename
            driving_name = os.path.splitext(driving_video)[0]
            input_name = os.path.splitext(os.path.basename(current_input_image))[0]
            output_filename = f"{input_name}--{driving_name}.mp4"
            output_chunk_path = os.path.join(OUTPUT_DIR, output_filename)

            if not os.path.isfile(output_chunk_path):
                print(f"[ERROR] Expected output file not found: {output_chunk_path}")
                sys.exit(1)

            print(f"[INFO] Saved chunk as {output_chunk_path}")

            # Extract last frame and use it for the next chunk
            extract_last_frame(output_chunk_path, LAST_FRAME_IMAGE)
            current_input_image = LAST_FRAME_IMAGE

            generated_chunks.append(output_chunk_path)
            chunk_index += 1

        # === Merge current batch ===
        merged_output_name = f"chunk{video_index}.mp4"
        merged_output_path = os.path.join(STREAM_OUTPUT_DIR, merged_output_name)
        merge_list_path = os.path.join(OUTPUT_DIR, f"merge_list_{video_index}.txt")

        with open(merge_list_path, "w") as f:
            for chunk_path in generated_chunks:
                rel_path = os.path.relpath(chunk_path, OUTPUT_DIR)
                f.write(f"file '{rel_path}'\n")

        merge_cmd = (
            f"ffmpeg -y -f concat -safe 0 -i \"{merge_list_path}\" "
            f"-c:v copy -c:a aac -strict experimental \"{merged_output_path}\""
        )

        run(merge_cmd)

        if os.path.isfile(merged_output_path):
            print(f"[SUCCESS] Saved merged video to stream: {merged_output_path}")
        else:
            print("[ERROR] Failed to create merged video")

        # === Cleanup temp_outputs ===
        for file in os.listdir(OUTPUT_DIR):
            file_path = os.path.join(OUTPUT_DIR, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"[WARN] Failed to delete {file_path}: {e}")

        video_index += 1

    print(f"[COMPLETE] Reached video limit ({video_limit}). Generation stopped.")


if __name__ == "__main__":
    print(f"[INFO] This script is meant to be called externally")
