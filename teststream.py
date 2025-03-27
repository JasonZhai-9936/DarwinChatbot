import os
import shutil

# === CONFIG ===
STREAM_DIR = os.path.join("outputs", "stream")
M3U8_PATH = os.path.join(STREAM_DIR, "playlist.m3u8")
STARTER_CHUNK_DIR = os.path.join("outputs", "generate_starter_chunks")
STARTER_CHUNKS = [
    "starter_chunk1.ts",
    "starter_chunk2.ts",
    "starter_chunk3.ts"
]

# Ensure stream dir exists
os.makedirs(STREAM_DIR, exist_ok=True)

# Start fresh playlist
with open(M3U8_PATH, "w") as f:
    f.write("#EXTM3U\n")
    f.write("#EXT-X-VERSION:3\n")
    f.write("#EXT-X-TARGETDURATION:5\n")
    f.write("#EXT-X-MEDIA-SEQUENCE:0\n")

    for chunk in STARTER_CHUNKS:
        chunk_path = os.path.join(STARTER_CHUNK_DIR, chunk)
        if not os.path.exists(chunk_path):
            print(f"[ERROR] Starter chunk not found: {chunk_path}")
            continue

        dest_path = os.path.join(STREAM_DIR, chunk)
        if not os.path.exists(dest_path):
            shutil.copyfile(chunk_path, dest_path)

        f.write(f"#EXTINF:5.0,\n{chunk}\n")
        print(f"[INFO] Added {chunk} to playlist")
        
        
# Write final chunk entries
with open(M3U8_PATH, "a") as f:
    for chunk in STARTER_CHUNKS:
        f.write(f"#EXTINF:5.0,\n{chunk}\n")
    f.write("#EXT-X-ENDLIST\n")  # ⬅️ This makes it VOD-style

print("[✅ DONE] teststream.py finished. Playlist written.")
