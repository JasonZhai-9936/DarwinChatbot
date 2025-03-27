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

# === Input chunk ===
input_chunk = os.path.join(STARTER_CHUNK_DIR, "starter_chunk1.ts")

if not os.path.exists(input_chunk):
    print("[ERROR] starter_chunk1.ts not found.")
    exit(1)

# Use a fixed duration (or use get_duration(input_chunk) if needed)
duration = 20

# === Insert starter1.ts and delete it quickly to simulate early segment loss ===
starter1_name = "starter1.ts"
starter1_path = os.path.join(STREAM_DIR, starter1_name)

shutil.copyfile(input_chunk, starter1_path)

with open(M3U8_PATH, "a") as f:
    f.write(f"#EXTINF:{duration},\n{starter1_name}\n")

with open(STREAM_LOG, "a") as f:
    f.write(f"[INIT] {starter1_name} inserted (to be deleted early)\n")

print(f"[INFO] Inserted {starter1_name} → duration {duration}s")
time.sleep(1)
os.remove(starter1_path)
print(f"[INFO] Deleted {starter1_name} before playback reached it")

# === Continue with repeating and testing mid-stream deletions ===
repeat_count = 5

for i in range(2, repeat_count + 2):  # start at 2 to avoid conflict with starter1.ts
    dest_name = f"starter{i}.ts"
    dest_path = os.path.join(STREAM_DIR, dest_name)

    shutil.copyfile(input_chunk, dest_path)

    with open(M3U8_PATH, "a") as f:
        f.write("#EXT-X-DISCONTINUITY\n")
        f.write(f"#EXTINF:{duration},\n{dest_name}\n")

    with open(STREAM_LOG, "a") as f:
        f.write(f"[REPEAT] {dest_name} inserted\n")

    print(f"[INFO] Inserted {dest_name} → duration {duration}s")

    if i in [2, 3]:  # simulate deletion and re-addition
        time.sleep(2)
        os.remove(dest_path)
        print(f"[INFO] Deleted {dest_name}")
        time.sleep(1)
        shutil.copyfile(input_chunk, dest_path)
        print(f"[INFO] Re-added {dest_name}")

    time.sleep(2)

print("[✅ DONE] Repeated chunk streaming completed.")
