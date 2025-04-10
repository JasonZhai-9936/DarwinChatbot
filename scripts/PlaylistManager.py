import os
import json
import random
import glob

PLAYLIST_DIR = os.path.join("stream", "playlist")
os.makedirs(PLAYLIST_DIR, exist_ok=True)
PLAYLIST_PATH = os.path.join(PLAYLIST_DIR, "playlist.json")

# === New Directory Structure ===
CHUNKS_BASE_DIR = os.path.join("stream", "chunks")
IMG2VID_CHUNKS_DIR = os.path.join(CHUNKS_BASE_DIR, "img2vid_chunks")
LIVE_DIR = os.path.join("stream", "live")

# === Idle Playlist Config ===
IDLE_SOURCES = {
    "img2vid": IMG2VID_CHUNKS_DIR,
}
IDLE_ODDS = [1.0]  # Only img2vid chunks

# === Response Playlist Config ===
RESPONSE_SOURCES = {
    "img2vid": IMG2VID_CHUNKS_DIR,
}
RESPONSE_ODDS = [1.0]  # Only img2vid chunks

# Define supported file extensions
SUPPORTED_EXTENSIONS = [".mp4", ".gif"]

def ensure_directories_exist():
    """Ensure all required directories exist"""
    os.makedirs(PLAYLIST_DIR, exist_ok=True)
    os.makedirs(CHUNKS_BASE_DIR, exist_ok=True)
    os.makedirs(IMG2VID_CHUNKS_DIR, exist_ok=True)

def is_supported_file(filename):
    """Check if the file has a supported extension"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def idle_playlist_maker():
    """Create a playlist for idle mode"""
    ensure_directories_exist()
    playlist = []
    source_keys = list(IDLE_SOURCES.keys())

    # Only grab from img2vid_chunks
    source_key = "img2vid"
    source_dir = IDLE_SOURCES[source_key]
        
    # Skip if directory doesn't exist or is empty
    if not os.path.exists(source_dir):
        print(f"[ERROR] Directory {source_dir} does not exist or is empty.")
        return

    # Find all supported files (mp4 and gif)
    files = [f for f in os.listdir(source_dir) if is_supported_file(f)]
    if files:
        # Select 7 random files
        selected_files = random.sample(files, 7)  # Grab 7 random files
        # Adjust path to use the new structure
        for selected in selected_files:
            playlist.append(os.path.join("chunks", "img2vid_chunks", selected))

    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[PLAYLIST] Idle playlist updated with {len(playlist)} items.")

def response_playlist_maker():
    """Create a playlist for response mode"""
    ensure_directories_exist()
    playlist = []
    source_keys = list(RESPONSE_SOURCES.keys())

    # Only grab from img2vid_chunks
    source_key = "img2vid"
    source_dir = RESPONSE_SOURCES[source_key]
        
    # Skip if directory doesn't exist or is empty
    if not os.path.exists(source_dir):
        print(f"[ERROR] Directory {source_dir} does not exist or is empty.")
        return

    # Find all supported files (mp4 and gif)
    files = [f for f in os.listdir(source_dir) if is_supported_file(f)]
    if files:
        # Select 7 random files
        selected_files = random.sample(files, 7)  # Grab 7 random files
        # Adjust path to use the new structure
        for selected in selected_files:
            playlist.append(os.path.join("chunks", "img2vid_chunks", selected))

    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[PLAYLIST] Response playlist created with {len(playlist)} items.")

def create_lipsync_playlist():
    """
    Creates a playlist starting with the most recent video from the live directory,
    followed by random videos from img2vid_chunks.
    """
    ensure_directories_exist()
    playlist = []
    source_keys = list(RESPONSE_SOURCES.keys())
    
    # Find the most recent video in the live directory
    video_files = []
    for ext in SUPPORTED_EXTENSIONS:
        video_files.extend(glob.glob(os.path.join(LIVE_DIR, f"*{ext}")))
    
    if video_files:
        # Get the most recent video file
        latest_video = max(video_files, key=os.path.getctime)
        latest_video_name = os.path.basename(latest_video)
        # Add this as the first item in the playlist
        playlist.append(os.path.join("live", latest_video_name))
        print(f"[PLAYLIST] Added latest video to playlist: {latest_video_name}")
    
    # Add 6 more random videos from img2vid_chunks
    source_key = "img2vid"
    source_dir = RESPONSE_SOURCES[source_key]
        
    # Skip if directory doesn't exist or is empty
    if not os.path.exists(source_dir):
        print(f"[ERROR] Directory {source_dir} does not exist or is empty.")
        return

    # Find all supported files (
