import subprocess
import os
import sys
import cv2
import random
import glob
import shutil

# Conda environment name
CONDA_ENV = "LivePortrait"

# 🛡️ Relaunch the script inside the Conda env if not already there
if os.environ.get("CONDA_DEFAULT_ENV") != CONDA_ENV:
    print(f"🔁 Not in Conda env '{CONDA_ENV}'. Relaunching...")
    subprocess.run(["conda", "run", "-n", CONDA_ENV, "python"] + sys.argv)
    sys.exit()

# File and directory paths
input_image = "Darwin5.png"
output_dir = "outputs"
last_frame_image = os.path.join(output_dir, "last_frame.png")
final_combined_video = os.path.join(output_dir, "finaloutput.mp4")
merge_list_file = os.path.join(output_dir, "merge_list.txt")

# Ensure outputs folder exists
os.makedirs(output_dir, exist_ok=True)

priority_animations = ["d0.pkl", "d1.pkl", "d12.pkl"]
animations = [
    "d0.mp4", "d0.pkl", "d1.pkl", "d10.mp4", "d10.pkl",
    "d11.mp4", "d12.mp4", "d12.pkl", "d13.mp4", "d14.mp4",
    "d18.mp4", "d18.pkl", "d19.mp4", "d19.pkl", "d2.pkl",
    "d20.mp4", "d3.mp4", "d5.pkl", "d6.mp4",
    "d7.pkl", "d8.pkl", "d9.mp4"
]

num_iterations = 3
used_priority_animations = set()
generated_videos = []

def run(command, cwd=None):
    print(f"🟢 Running: {' '.join(command) if isinstance(command, list) else command}")
    try:
        subprocess.run(command, cwd=cwd, shell=isinstance(command, str), check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def get_latest_output(directory):
    video_files = glob.glob(os.path.join(directory, "*.mp4"))
    if not video_files:
        print(f"❌ Error: No MP4 files found in {directory}")
        sys.exit(1)
    return max(video_files, key=os.path.getctime)

def extract_last_frame(video_path, output_image_path):
    print(f"🎞️ Extracting last frame from {video_path} to {output_image_path}")
    command = (
        f"ffmpeg -y -sseof -3 -i \"{video_path}\" -vframes 1 \"{output_image_path}\""
    )
    run(command)

def safe_remove(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"🗑️ Removed existing file: {filepath}")

# Cleanup old outputs
for i in range(num_iterations):
    safe_remove(os.path.join(output_dir, f"chunk{i+1}.mp4"))
safe_remove(final_combined_video)
safe_remove(last_frame_image)
safe_remove(merge_list_file)

# Main loop
current_input_image = input_image

for i in range(num_iterations):
    print(f"\n--- Iteration {i+1}/{num_iterations} ---")
    if len(used_priority_animations) < len(priority_animations):
        available_priority = list(set(priority_animations) - used_priority_animations)
        driving_video = random.choice(available_priority)
        used_priority_animations.add(driving_video)
    else:
        driving_video = random.choice(animations)

    driving_video_path = f"assets/examples/driving/{driving_video}"
    temp_output_dir = os.path.join(output_dir, f"temp_output_{i}")
    os.makedirs(temp_output_dir, exist_ok=True)

    print(f"🎬 Driving video: {driving_video_path}")
    run(["python", "inference.py", "-s", current_input_image, "-d", driving_video_path, "-o", temp_output_dir])

    if not os.path.isdir(temp_output_dir):
        print(f"❌ Error: Expected output directory {temp_output_dir} does not exist")
        sys.exit(1)

    output_video = get_latest_output(temp_output_dir)
    chunk_name = os.path.join(output_dir, f"chunk{i+1}.mp4")
    os.rename(output_video, chunk_name)
    print(f"📼 Renamed output to {chunk_name}")
    generated_videos.append(chunk_name)

    extract_last_frame(chunk_name, last_frame_image)
    current_input_image = last_frame_image

    shutil.rmtree(temp_output_dir)

# Merge chunks into final output
print("\n🎥 Merging chunks into final output...")
with open(merge_list_file, "w") as f:
    for vid in generated_videos:
        f.write(f"file '{os.path.basename(vid)}'\n")

run(f"ffmpeg -y -f concat -safe 0 -i {merge_list_file} -c copy {final_combined_video}")

if not os.path.isfile(final_combined_video):
    print(f"❌ Error: Merging failed, {final_combined_video} not created")
    sys.exit(1)

print(f"✅ Final combined video saved as {final_combined_video}")
