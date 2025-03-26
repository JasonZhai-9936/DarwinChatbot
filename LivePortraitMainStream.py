import subprocess
import os
import sys
import random
import glob
import shutil
import json

# ==== CONFIG ====
APPLY_SLOWDOWN = True
TARGET_SPEED_PERCENT = 70
STARTER_CHUNK_COUNT = 5

# =================

CONDA_ENV = "LivePortrait"
REPO_DIR = "LivePortrait"
INFERENCE_SCRIPT = os.path.join(REPO_DIR, "inference.py")
ASSETS_DIR = os.path.join(REPO_DIR, "assets", "drivers")
OUTPUT_DIR = os.path.join(REPO_DIR, "outputs")
INPUT_IMAGE = os.path.join(REPO_DIR, "assets", "prompts", "Darwin4.png")
LAST_FRAME_IMAGE = os.path.join(OUTPUT_DIR, "last_frame.png")
FINAL_VIDEO = os.path.join(OUTPUT_DIR, "finaloutput.mp4")
MERGE_LIST = os.path.join(OUTPUT_DIR, "merge_list.txt")
STREAM_DIR = os.path.join("outputs", "stream")
M3U8_PATH = os.path.join(STREAM_DIR, "playlist.m3u8")
STREAM_LOG = os.path.join(STREAM_DIR, "stream_log.txt")
STARTER_CHUNK_DIR = os.path.join("outputs", "generate_starter_chunks")


IS_WIN = sys.platform.startswith("win")
FFMPEG = os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe" if IS_WIN else "ffmpeg")
FFPROBE = os.path.join("tools", "ffmpeg", "bin", "ffprobe.exe" if IS_WIN else "ffprobe")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STREAM_DIR, exist_ok=True)

# Clean up leftover chunk files from previous runs
for f in os.listdir(OUTPUT_DIR):
    if f.startswith("chunk") and f.endswith(".mp4"):
        os.remove(os.path.join(OUTPUT_DIR, f))

# Start fresh log
with open(STREAM_LOG, "w") as f:
    f.write("=== STREAM SESSION START ===\n")

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
    if isinstance(command, list):
        command = ' '.join(f'"{c}"' if ' ' in c else c for c in command)
    print(f"[RUN] {command}")
    try:
        subprocess.run(command, cwd=cwd, shell=True, check=True)
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
    command = f"{FFMPEG} -y -sseof -3 -i \"{video_path}\" -vframes 1 \"{output_image_path}\""
    run(command)

def safe_remove(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"[INFO] Removed file: {filepath}")

def get_duration(filepath):
    result = subprocess.run(
        [
            FFPROBE, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", filepath
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    duration = json.loads(result.stdout)["format"]["duration"]
    return round(float(duration), 3)

def has_audio_stream(filepath):
    result = subprocess.run(
        [
            FFPROBE, "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "default=nw=1",
            filepath
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return b"codec_type=audio" in result.stdout

def slow_down_video(input_path, output_path, speed_percent):
    speed_factor = speed_percent / 100.0
    video_filter = f"setpts={1/speed_factor}*PTS"
    has_audio = has_audio_stream(input_path)

    if has_audio:
        audio_filters = []
        tempo = speed_factor
        while tempo < 0.5:
            audio_filters.append("atempo=0.5")
            tempo *= 2
        while tempo > 2.0:
            audio_filters.append("atempo=2.0")
            tempo /= 2
        audio_filters.append(f"atempo={tempo}")
        audio_filter_chain = ",".join(audio_filters)

        cmd = [
            FFMPEG, "-y", "-i", input_path,
            "-filter_complex", f"[0:v]{video_filter}[v];[0:a]{audio_filter_chain}[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            output_path
        ]
    else:
        cmd = [
            FFMPEG, "-y", "-i", input_path,
            "-filter:v", video_filter,
            "-c:v", "libx264",
            "-an",
            output_path
        ]

    run(cmd)
    print(f"[DEBUG] slowdown applied → checking duration...")
    print(f"[DEBUG] New file: {output_path}, duration: {get_duration(output_path)}s")

starter_chunks = [
    os.path.join(STARTER_CHUNK_DIR, f)
    for f in os.listdir(STARTER_CHUNK_DIR)
    if f.startswith("starter_chunk") and f.endswith(".ts")
]

current_input_image = INPUT_IMAGE
for i in range(num_iterations):
    print(f"\n[STEP] Iteration {i+1}/{num_iterations}")

    inserted_starters = random.sample(starter_chunks, STARTER_CHUNK_COUNT)
    with open(M3U8_PATH, "a") as f:
        for starter in inserted_starters:
            f.write(f"#EXTINF:5.0,\n{starter}\n")
    with open(STREAM_LOG, "a") as f:
        for starter in inserted_starters:
            f.write(f"[STARTER] {starter}\n")
    print(f"[INFO] Inserted starter chunks: {inserted_starters}")

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
    if os.path.exists(chunk_name):
        os.remove(chunk_name)
    os.rename(output_video, chunk_name)

    if APPLY_SLOWDOWN:
        slowed_chunk = os.path.join(OUTPUT_DIR, f"chunk{i+1}_slow.mp4")
        slow_down_video(chunk_name, slowed_chunk, TARGET_SPEED_PERCENT)
        os.remove(chunk_name)
        os.rename(slowed_chunk, chunk_name)

    stream_chunk = os.path.join(STREAM_DIR, f"chunk{i+1}.ts")
    ffmpeg_cmd = f"{FFMPEG} -y -i {chunk_name} -c:v copy -c:a copy -bsf:v h264_mp4toannexb -f mpegts {stream_chunk}"
    run(ffmpeg_cmd)

    duration = get_duration(stream_chunk)

    with open(M3U8_PATH, "r+") as f:
        lines = f.readlines()
        if len(lines) >= 6:
            lines = lines[:-6]
        lines.append(f"#EXTINF:{duration},\nchunk{i+1}.ts\n")
        f.seek(0)
        f.writelines(lines)
        f.truncate()

    with open(STREAM_LOG, "a") as f:
        f.write(f"[REAL] chunk{i+1}.ts from {driving_video}\n")

    print(f"[INFO] Replaced starter chunks with real chunk{i+1}.ts")

    extract_last_frame(chunk_name, LAST_FRAME_IMAGE)
    current_input_image = LAST_FRAME_IMAGE
    shutil.rmtree(temp_output_dir)

    generated_videos.append(chunk_name)

print("\n[INFO] Merging chunks into final output...")
with open(MERGE_LIST, "w") as f:
    for vid in generated_videos:
        f.write(f"file '{os.path.basename(vid)}'\n")

run(f"{FFMPEG} -y -f concat -safe 0 -i {MERGE_LIST} -c copy {FINAL_VIDEO}")

if not os.path.isfile(FINAL_VIDEO):
    print(f"[ERROR] Merging failed. {FINAL_VIDEO} not created.")
    sys.exit(1)

print(f"[SUCCESS] Final combined video saved as {FINAL_VIDEO}")
