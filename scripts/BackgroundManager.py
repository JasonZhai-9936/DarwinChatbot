import os
import random
import json
import glob
import time

# Define directory structure
OVERLAY_DIR = os.path.join("stream", "Overlay_Assets", "Beagle Voyage")
BACKGROUND_PLAYLIST_DIR = os.path.join("stream", "playlist")
BACKGROUND_PLAYLIST_PATH = os.path.join(BACKGROUND_PLAYLIST_DIR, "background_playlist.json")

# For supported file extensions
SUPPORTED_EXTENSIONS = [".mp4"]

def ensure_directories_exist():
    """Ensure all required directories exist"""
    os.makedirs(BACKGROUND_PLAYLIST_DIR, exist_ok=True)

def is_supported_file(filename):
    """Check if the file has a supported extension"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def create_background_playlist(num_clips=5):
    """Generate a playlist with random background videos"""
    ensure_directories_exist()
    
    # Get all supported files from the Beagle Voyage directory
    if not os.path.exists(OVERLAY_DIR):
        print(f"[ERROR] Overlay directory {OVERLAY_DIR} does not exist.")
        return []
    
    # Get all supported video files from the directory
    files = []
    for root, dirs, filenames in os.walk(OVERLAY_DIR):
        for filename in filenames:
            if is_supported_file(filename):
                # Get path relative to stream directory
                rel_path = os.path.join(root, filename)
                # Make sure we use forward slashes for web paths
                rel_path = os.path.relpath(rel_path, "stream").replace("\\", "/")
                files.append(rel_path)
    
    if not files:
        print(f"[ERROR] No video files found in {OVERLAY_DIR}.")
        return []
    
    # Select random files for the playlist
    if len(files) <= num_clips:
        playlist = files.copy()  # Use all files if we have fewer than requested
    else:
        playlist = random.sample(files, num_clips)
    
    # Save the playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)
    
    print(f"[BACKGROUND] New background playlist created with {len(playlist)} videos")
    return playlist

def initialize_background_player():
    """Initialize the background player with a delay"""
    # Create an empty playlist initially (for blank start)
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump([], f)
    
    # Schedule the actual playlist creation after a delay
    def delayed_playlist_creation():
        time.sleep(3)  # 3-second delay
        create_background_playlist(num_clips=5)
        print("[BACKGROUND] Background videos now playing after delay")
    
    # Start the delayed playlist creation in a separate thread
    import threading
    bg_thread = threading.Thread(target=delayed_playlist_creation)
    bg_thread.daemon = True
    bg_thread.start()
    
    return True