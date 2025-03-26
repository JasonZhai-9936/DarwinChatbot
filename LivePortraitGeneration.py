# This .py handles various generations, such as generating starter chunks

import os
import subprocess
import random
import shutil
import glob

# === CONFIG ===
NUM_ITERATIONS = 3
OUTPUT_SUBDIR = "generate_starter_chunks"
OUTPUT_DIR = os.path.join("outputs", OUTPUT_SUBDIR)
CONDA_ENV = "LivePortrait"
REPO_DIR = "LivePortrait"
INFERENCE_SCRIPT = os.path.join(REPO_DIR, "inference.py")
INPUT_IMAGE = os.path.join(REPO_DIR, "assets", "prompts", "Darwin4.png")
ASSETS_DIR = os.path.join(REPO_DIR, "assets", "drivers")
FFMPEG = os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
LAST_FRAME_IMAGE = os.path.join(OUTPUT_DIR, "last_frame.png")

# === OPTIONAL SLOWDOWN SETTINGS ===
APPLY_SLOWDOWN = True
TARGET_SPEED_PERCENT = 70

priority_animations = ["d19.mp4", "d0.mp4", "d18.mp4", "d13.mp4", "d3.mp4"]
animations = [
    "d0.mp4", "d0.pkl", "d1.pkl", "d10.mp4", "d10.pkl",
    "d11.mp4", "d12.mp4", "d12.pkl", "d13.mp4", "d14.mp4",
    "d18.mp4", "d18.pkl", "d19.mp4", "d19.pkl", "d2.pkl",
    "d20.mp4", "d3.mp4", "d5.pkl", "d6.mp4",
    "d7.pkl", "d8.pkl", "d9.mp4"
]

used_priority_animations = set()

os.makedirs(OUTPUT_DIR, exist_ok=True)

def run(cmd, cwd=None):
    print(f"[RUNNING] {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)

def extract_last_frame(video_path, out_image):
    run([FFMPEG, "-y", "-sseof", "-3", "-i", video_path, "-vframes", "1", out_image])

def has_audio_stream(filepath):
    result = subprocess.run(
        [
            FFMPEG, "-v", "error",
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
        audio_chain = ",".join(audio_filters)

        cmd = [
            FFMPEG, "-y", "-i", input_path,
            "-filter_complex", f"[0:v]{video_filter}[v];[0:a]{audio_chain}[a]",
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

def get_next_chunk_index():
    existing = glob.glob(os.path.join(OUTPUT_DIR, "starter_chunk*.ts"))
    indexes = []
    for f in existing:
        name = os.path.splitext(os.path.basename(f))[0]
        parts = name.replace("starter_chunk", "")
        if parts.isdigit():
            indexes.append(int(parts))
    return max(indexes + [0]) + 1

def generate_starter_chunks():
    current_input_image = INPUT_IMAGE

    # === CLEANUP OLD TEMP CHUNKS ===
    print("[CLEANUP] Removing old temp_starter_chunk*.ts/.mp4...")
    for f in glob.glob(os.path.join(OUTPUT_DIR, "temp_starter_chunk*.ts")) + glob.glob(os.path.join(OUTPUT_DIR, "temp_starter_chunk*.mp4")):
        os.remove(f)

    # === DETERMINE FINAL STARTER_CHUNK INDEX ===
    existing_chunks = glob.glob(os.path.join(OUTPUT_DIR, "starter_chunk*.ts"))
    existing_indexes = []
    for f in existing_chunks:
        name = os.path.splitext(os.path.basename(f))[0]
        idx = name.replace("starter_chunk", "")
        if idx.isdigit():
            existing_indexes.append(int(idx))
    final_index = max(existing_indexes + [0]) + 1  # this run's starter_chunk index

    temp_ts_paths = []

    for i in range(NUM_ITERATIONS):
        print(f"\n[GENERATION] Iteration {i+1}/{NUM_ITERATIONS}")
        if len(used_priority_animations) < len(priority_animations):
            available_priority = list(set(priority_animations) - used_priority_animations)
            driving_video_name = random.choice(available_priority)
            used_priority_animations.add(driving_video_name)
        else:
            driving_video_name = random.choice(animations)

        driving_video = os.path.join(ASSETS_DIR, driving_video_name)
        print(f"[INFO] Using driving video: {driving_video_name}")

        temp_dir = os.path.join(OUTPUT_DIR, f"temp_{i}")
        os.makedirs(temp_dir, exist_ok=True)

        run([
            "conda", "run", "-n", CONDA_ENV, "python", INFERENCE_SCRIPT,
            "-s", current_input_image,
            "-d", driving_video,
            "-o", temp_dir,
            "--animation_region", "all"
        ])

        mp4_files = glob.glob(os.path.join(temp_dir, "*.mp4"))
        if not mp4_files:
            print(f"[ERROR] No output video found in {temp_dir}")
            continue

        temp_mp4 = os.path.join(OUTPUT_DIR, f"temp_starter_chunk{i+1}.mp4")
        shutil.move(mp4_files[0], temp_mp4)

        # Optional slowdown
        if APPLY_SLOWDOWN:
            slowed_mp4 = os.path.join(OUTPUT_DIR, f"temp_starter_chunk{i+1}_slow.mp4")
            slow_down_video(temp_mp4, slowed_mp4, TARGET_SPEED_PERCENT)
            os.remove(temp_mp4)
            os.rename(slowed_mp4, temp_mp4)

        temp_ts = os.path.join(OUTPUT_DIR, f"temp_starter_chunk{i+1}.ts")
        run([
            FFMPEG, "-y", "-i", temp_mp4, "-c:v", "copy", "-c:a", "copy",
            "-bsf:v", "h264_mp4toannexb", "-f", "mpegts", temp_ts
        ])
        temp_ts_paths.append(temp_ts)

        extract_last_frame(temp_mp4, LAST_FRAME_IMAGE)
        current_input_image = LAST_FRAME_IMAGE

        shutil.rmtree(temp_dir)

    # === JOIN TEMP CHUNKS INTO FINAL starter_chunkX.ts/mp4 ===
    print("\n[MERGE] Combining temp_starter_chunk*.ts into final starter_chunk...")
    inputs_txt = os.path.join(OUTPUT_DIR, "inputs.txt")
    with open(inputs_txt, "w") as f:
        for path in temp_ts_paths:
            rel_path = os.path.relpath(path, OUTPUT_DIR).replace("\\", "/")
            f.write(f"file '{rel_path}'\n")

    final_ts = os.path.join(OUTPUT_DIR, f"starter_chunk{final_index}.ts")
    final_mp4 = os.path.join(OUTPUT_DIR, f"starter_chunk{final_index}.mp4")

    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", "inputs.txt",
        "-c", "copy", os.path.basename(final_ts)
    ], cwd=OUTPUT_DIR)

    print("\n[EXPORT] Creating starter_chunk MP4 from TS...")
    run([
        FFMPEG, "-y", "-i", os.path.basename(final_ts),
        "-c", "copy", os.path.basename(final_mp4)
    ], cwd=OUTPUT_DIR)

    print(f"[✅ COMPLETE] Generated:\n  → {final_ts}\n  → {final_mp4}")

if __name__ == "__main__":
    generate_starter_chunks()
