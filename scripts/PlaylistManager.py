import os
import json
import random

PLAYLIST_DIR = os.path.join("stream", "playlist")
os.makedirs(PLAYLIST_DIR, exist_ok=True)
PLAYLIST_PATH = os.path.join(PLAYLIST_DIR, "playlist.json")


# === Idle Playlist Config ===
IDLE_SOURCES = {
    "idle_chunks": os.path.join("stream", "idle_chunks"),
    "talking_chunks": os.path.join("stream", "talking_chunks"),
    "live": os.path.join("stream", "live"),
}
#IDLE_ODDS = [0.33, 0.33, 0.34]  # idle, talking, live
IDLE_ODDS = [0, 0, 1]  # idle, talking, live


# === Response Playlist Config ===
RESPONSE_SOURCES = {
    "idle_chunks": os.path.join("stream", "idle_chunks"),
    "talking_chunks": os.path.join("stream", "talking_chunks"),
    "live": os.path.join("stream", "live"),
}
RESPONSE_ODDS = [0.33, 0.33, 0.34]  # idle, talking, live


def idle_playlist_maker():
    playlist = []
    source_keys = list(IDLE_SOURCES.keys())

    for _ in range(5):
        source_key = random.choices(source_keys, weights=IDLE_ODDS)[0]
        source_dir = IDLE_SOURCES[source_key]
        files = [f for f in os.listdir(source_dir) if f.endswith(".mp4")]
        if files:
            selected = random.choice(files)
            playlist.append(os.path.join(source_key, selected))

    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[PLAYLIST] Idle playlist updated with {len(playlist)} items.")


def response_playlist_maker():
    playlist = []
    source_keys = list(RESPONSE_SOURCES.keys())

    for _ in range(5):
        source_key = random.choices(source_keys, weights=RESPONSE_ODDS)[0]
        source_dir = RESPONSE_SOURCES[source_key]
        files = [f for f in os.listdir(source_dir) if f.endswith(".mp4")]
        if files:
            selected = random.choice(files)
            playlist.append(os.path.join(source_key, selected))

    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[PLAYLIST] Response playlist created with {len(playlist)} items.")
