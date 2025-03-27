import os
import shutil
import time
import json
import subprocess

STREAM_DIR = os.path.join("outputs", "stream")
STARTER_CHUNK_DIR = os.path.join("outputs", "generate_starter_chunks")
M3U8_PATH = os.path.join(STREAM_DIR, "playlist.m3u8")
STREAM_LOG = os.path.join(STREAM_DIR, "stream_log.txt")
FFMPEG = os.path.join("tools", "ffmpeg", "bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
FFPROBE = os.path.join("tools", "ffmpeg", "bin", "ffprobe.exe" if os.name == "nt" else "ffprobe")

os.makedirs(STREAM_DIR, exist_ok=True)

def get_duration(filepath):
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    duration = json.loads(result.stdout)["format"]["duration"]
    return round(float(duration), 3)

def reencode_chunk(input_path, output_path):
    command = [
        FFMPEG,
        "-y", "-i", input_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "main",
        "-level", "3.1",
        "-r", "24",
        "-g", "48",
        "-keyint_min", "48",
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "128k",
        "-ac", "2",
        "-f", "mpegts",
        "-muxpreload", "0",
        "-muxdelay", "0",
        output_path
    ]
    subprocess.run(command, check=True)

# === Clean and initialize stream directory ===
for f in os.listdir(STREAM_DIR):
    if f.endswith(".ts") or f == "playlist.m3u8":
        os.remove(os.path.join(STREAM_DIR, f))

with open(M3U8_PATH, "w") as f:
    f.write("#EXTM3U\n")
    f.write("#EXT-X-VERSION:3\n")
    f.write("#EXT-X-ALLOW-CACHE:NO\n")
    f.write("#EXT-X-PLAYLIST-TYPE:EVENT\n")
    f.write("#EXT-X-TARGETDURATION:45\n")
    f.write("#EXT-X-MEDIA-SEQUENCE:0\n")

with open(STREAM_LOG, "w") as f:
    f.write("=== STREAM TEST (REPEAT MODE) START ===\n")

# === Repeatedly reencode starter_chunk1.ts ===
input_chunk = os.path.join(STARTER_CHUNK_DIR, "starter_chunk1.ts")

if not os.path.exists(input_chunk):
    print("[ERROR] starter_chunk1.ts not found.")
    exit(1)

repeat_count = 5  # how many times to repeat the chunk

for i in range(repeat_count):
    dest_name = f"starter{i+1}.ts"
    dest_path = os.path.join(STREAM_DIR, dest_name)

    try:
        reencode_chunk(input_chunk, dest_path)
    except subprocess.CalledProcessError:
        print(f"[ERROR] Re-encoding failed on repetition {i+1}")
        continue

    duration = get_duration(dest_path)

    with open(M3U8_PATH, "a") as f:
        if i > 0:
            f.write("#EXT-X-DISCONTINUITY\n")
        f.write(f"#EXTINF:{duration},\n{dest_name}\n")

    with open(STREAM_LOG, "a") as f:
        f.write(f"[REPEAT] {dest_name} inserted\n")

    print(f"[INFO] Inserted {dest_name} → duration {duration}s")
    time.sleep(5)  # simulate live delay

print("[✅ DONE] Repeated chunk streaming completed.")
