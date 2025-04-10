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

def get_random_files_from_dir(directory, num_files=7):
    """Helper function to get 'num_files' random supported files from the given directory."""
    if not os.path.exists(directory):
        return []

    # Find all supported files (mp4 and gif)
    files = [f for f in os.listdir(directory) if is_supported_file(f)]
    
    if len(files) < num_files:
        # If there are fewer than the requested files, return them all
        return files

    # Select 'num_files' random files
    return random.sample(files, num_files)

def idle_playlist_maker():
    """Create a playlist for idle mode"""
    ensure_directories_exist()
    playlist = []
    
    # Get 7 random files from the img2vid_chunks directory
    files = get_random_files_from_dir(IMG2VID_CHUNKS_DIR)
    
    for selected in files:
        # Adjust path to use the new structure
        playlist.append(os.path.join("chunks", "img2vid_chunks", selected))
    
    # Save the playlist
    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[PLAYLIST] Idle playlist updated with {len(playlist)} items.")

def response_playlist_maker():
    """Create a playlist for response mode"""
    ensure_directories_exist()
    playlist = []
    
    # Get 7 random files from the img2vid_chunks directory
    files = get_random_files_from_dir(IMG2VID_CHUNKS_DIR)
    
    for selected in files:
        # Adjust path to use the new structure
        playlist.append(os.path.join("chunks", "img2vid_chunks", selected))
    
    # Save the playlist
    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[PLAYLIST] Response playlist created with {len(playlist)} items.")

if __name__ == "__main__":
    # If this script is run directly, create fresh playlists
    idle_playlist_maker()
    response_playlist_maker()
    print("[INFO] Playlist creation complete")
