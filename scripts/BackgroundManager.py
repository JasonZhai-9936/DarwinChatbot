import os
import random
import json
import glob
import time

# Define directory structure
OVERLAY_DIR = os.path.join("stream", "Overlay_Assets", "Beagle Voyage")
BACKGROUND_PLAYLIST_DIR = os.path.join("stream", "playlist")
BACKGROUND_PLAYLIST_PATH = os.path.join(BACKGROUND_PLAYLIST_DIR, "background_playlist.json")

# Supported video and image extensions
SUPPORTED_EXTENSIONS = [".mp4", ".png", ".jpg", ".jpeg", ".webp"]

def ensure_directories_exist():
    """Ensure all required directories exist"""
    os.makedirs(BACKGROUND_PLAYLIST_DIR, exist_ok=True)

def is_supported_file(filename):
    """Check if the file has a supported extension"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def create_background_playlist(num_clips=10):
    """Generate a playlist with random background videos or images"""
    ensure_directories_exist()

    if not os.path.exists(OVERLAY_DIR):
        print(f"[ERROR] Overlay directory {OVERLAY_DIR} does not exist.")
        return []

    # Get all supported media files
    files = []
    for root, dirs, filenames in os.walk(OVERLAY_DIR):
        for filename in filenames:
            if is_supported_file(filename):
                rel_path = os.path.relpath(os.path.join(root, filename), "stream").replace("\\", "/")
                files.append(rel_path)

    if not files:
        print(f"[ERROR] No media files found in {OVERLAY_DIR}.")
        return []

    # Select random media files
    playlist = random.sample(files, min(num_clips, len(files)))

    # Save playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    print(f"[BACKGROUND] New background playlist created with {len(playlist)} items")
    return playlist

def initialize_background_player():
    """Initialize the background player with a delay"""
    # Start with an empty playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump([], f)

    def delayed_playlist_creation():
        time.sleep(3)  # Delay before generating playlist
        create_background_playlist(num_clips=5)
        print("[BACKGROUND] Background media now playing after delay")

    import threading
    bg_thread = threading.Thread(target=delayed_playlist_creation)
    bg_thread.daemon = True
    bg_thread.start()

    return True
