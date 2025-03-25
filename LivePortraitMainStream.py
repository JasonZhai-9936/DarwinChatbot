# Modified LivePortraitMain.py to support streaming with .ts chunks (HLS compatible + dynamic EXTINF)
import subprocess
import os
import sys
import random
import glob
import shutil
import json

CONDA_ENV = "LivePortrait"
REPO_DIR = "LivePortrait"
INFERENCE_SCRIPT = os.path.join(REPO_DIR, "inference.py")
ASSETS_DIR = os.path.join(REPO_DIR, "assets", "drivers")
OUTPUT_DIR = os.path.join(REPO_DIR, "outputs")
INPUT_IMAGE = os.path.join(REPO_DIR, "assets", "prompts", "Darwin4.png")
LAST_FRAME_IMAGE = os.path.join(OUTPUT_DIR, "last_frame.png")
FINAL_VIDEO = os.path.join(OUTPUT_DIR, "finaloutput.mp4")
MERGE_LIST = os.path.join(OUTPUT_DIR, "merge_list.txt")
STREAM_DIR = os.path.join("static", "stream")
M3U8_PATH = os.path.join(STREAM_DIR, "playlist.m3u8")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STREAM_DIR, exist_ok=True)

priority_animations = ["d19.mp4", "d0.mp4", "d12.mp4", "d11.mp4", "d3.mp4"]
animations = [
    "d0.mp4", "d0.pkl", "d1.pkl", "d10.mp4", "d10.pkl",
    "d11.mp4", "d12.mp4", "d12.pkl", "d13.mp4", "d14.mp4",
    "d18.mp4", "d18.pkl", "d19.mp4", "d19.pkl", "d2.pkl",
    "d20.mp4", "d3.mp4", "d5.pkl", "d6.mp4",
    "d7.pkl", "d8.pkl", "d9.mp4"
]

num_iterations = 5
used_priority_animations = set()
generated_videos = []

# Start fresh playlist
with open(M3U8_PATH, "w") as f:
    f.write("#EXTM3U\n")
    f.write("#EXT-X-VERSION:3\n")
    f.write("#EXT-X-TARGETDURATION:5\n")
    f.write("#EXT-X-MEDIA-SEQUENCE:0\n")

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

def safe_remove(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"[INFO] Removed file: {filepath}")

def get_duration(filepath):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", filepath
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    duration = json.loads(result.stdout)["format"]["duration"]
    return round(float(duration), 3)

# Clean old files
for i in range(num_iterations):
    safe_remove(os.path.join(OUTPUT_DIR, f"chunk{i+1}.mp4"))
    safe_remove(os.path.join(STREAM_DIR, f"chunk{i+1}.ts"))
safe_remove(FINAL_VIDEO)
safe_remove(LAST_FRAME_IMAGE)
safe_remove(MERGE_LIST)

current_input_image = INPUT_IMAGE
for i in range(num_iterations):
    print(f"\n[STEP] Iteration {i+1}/{num_iterations}")
    if len(used_priority_animations) < len(priority_animations):
        available_priority = list(set(priority_animations) - used_priority_animations)
        driving_video = random.choice(available_priority)
        used_priority_animations.add(driving_video)
    else:
        driving_video = random.choice(animations)

    driving_video_path = os.path.join(ASSETS_DIR, driving_video)
    temp_output_dir = os.path.join(OUTPUT_DIR, f"temp_output_{i}")
    os.makedirs(temp_output_dir, exist_ok=True)

    print(f"[INFO] Using driving video: {driving_video_path}")
    
    
    run([
    "conda", "run", "-n", CONDA_ENV, "python", INFERENCE_SCRIPT,
    "-s", current_input_image,
    "-d", driving_video_path,
    "-o", temp_output_dir,
    "--animation_region", "all"
])

    if not os.path.isdir(temp_output_dir):
        print(f"[ERROR] Expected output directory {temp_output_dir} does not exist")
        sys.exit(1)

    output_video = get_latest_output(temp_output_dir)
    chunk_name = os.path.join(OUTPUT_DIR, f"chunk{i+1}.mp4")
    os.rename(output_video, chunk_name)
    print(f"[INFO] Renamed output to {chunk_name}")
    generated_videos.append(chunk_name)

    # Convert to TS for streaming
    stream_chunk = os.path.join(STREAM_DIR, f"chunk{i+1}.ts")
    ffmpeg_cmd = f"ffmpeg -y -i {chunk_name} -c:v copy -c:a copy -bsf:v h264_mp4toannexb -f mpegts {stream_chunk}"
    run(ffmpeg_cmd)
    print(f"[INFO] Converted to TS format: {stream_chunk}")

       # Append to playlist with accurate EXTINF (no ENDLIST for live-style playback)
    duration = get_duration(stream_chunk)
    with open(M3U8_PATH, "r+") as f:
        lines = f.readlines()
        # remove any existing ENDLIST
        lines = [line for line in lines if line.strip() != "#EXT-X-ENDLIST"]
        lines.append(f"#EXTINF:{duration},\nchunk{i+1}.ts\n")
        f.seek(0)
        f.writelines(lines)
        f.truncate()

    extract_last_frame(chunk_name, LAST_FRAME_IMAGE)
    current_input_image = LAST_FRAME_IMAGE
    shutil.rmtree(temp_output_dir)

# Merge final video (not used for streaming, but kept for download)
print("\n[INFO] Merging chunks into final output...")
with open(MERGE_LIST, "w") as f:
    for vid in generated_videos:
        f.write(f"file '{os.path.basename(vid)}'\n")

run(f"ffmpeg -y -f concat -safe 0 -i {MERGE_LIST} -c copy {FINAL_VIDEO}")

if not os.path.isfile(FINAL_VIDEO):
    print(f"[ERROR] Merging failed. {FINAL_VIDEO} not created.")
    sys.exit(1)

print(f"[SUCCESS] Final combined video saved as {FINAL_VIDEO}")
