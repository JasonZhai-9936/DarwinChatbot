import os
import random
import json
import glob

# === Directory structure ===
OVERLAY_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream", "Overlay_Assets")
BACKGROUND_PLAYLIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream", "playlist")
BACKGROUND_PLAYLIST_PATH = os.path.join(BACKGROUND_PLAYLIST_DIR, "background_playlist.json")
SUPPORTED_EXTENSIONS = [".mp4", ".png", ".jpg", ".jpeg", ".webp", ".gif"]

def ensure_directories_exist():
    """Ensure required directories exist."""
    os.makedirs(BACKGROUND_PLAYLIST_DIR, exist_ok=True)

def is_supported_file(filename):
    """Check for supported media extensions."""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def get_available_folders():
    """Return folders inside the Overlay_Assets directory."""
    if not os.path.exists(OVERLAY_BASE_DIR):
        print(f"[ERROR] Overlay base directory {OVERLAY_BASE_DIR} does not exist.")
        return []
    folders = [f for f in os.listdir(OVERLAY_BASE_DIR) if os.path.isdir(os.path.join(OVERLAY_BASE_DIR, f))]
    print(f"[BACKGROUND] Available folders: {folders}")
    return folders

def select_relevant_folder(query_type, query_content):
    """Select a background folder based on query content."""
    if query_type == 1:
        print("[BACKGROUND] Generic query — skipping background selection.")
        return None

    available_folders = get_available_folders()
    if not available_folders:
        return None

    query_lower = query_content.lower()
    folder_keywords = {
        "beagle voyage": ["beagle", "voyage", "galapagos"],
        "darwin_family": ["family", "emma", "wife", "childhood", "children"],
        "darwin_himself": ["portrait", "biography", "life", "darwin"],
        "darwins finches": ["finch", "finches", "beak", "birds"],
        "evolution_conv_div": ["evolution", "divergence", "convergence", "species"],
        "natural_selection": ["natural selection", "adaptation", "survival", "competition"],
        "shropshire": ["shropshire", "england", "birthplace", "shrewsbury"],
        "tree_of_life": ["tree of life", "common ancestor"]
    }

    folder_scores = {folder: 0 for folder in available_folders}
    for folder, keywords in folder_keywords.items():
        if folder in available_folders:
            for keyword in keywords:
                if keyword in query_lower:
                    folder_scores[folder] += 1

    max_score = max(folder_scores.values()) if folder_scores else 0
    if max_score > 0:
        best_folders = [folder for folder, score in folder_scores.items() if score == max_score]
        selected = random.choice(best_folders)
        print(f"[BACKGROUND] Selected folder: {selected}")
        return selected

    if query_type in [2, 3]:
        fallback = random.choice(available_folders)
        print(f"[BACKGROUND] No match found. Fallback folder: {fallback}")
        return fallback

    return None

def create_background_playlist_for_folder(folder_name, shuffle=True):
    """Create a background playlist from media in the given folder."""
    ensure_directories_exist()

    if not folder_name:
        with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
            json.dump([], f)
        print("[BACKGROUND] Empty playlist created.")
        return []

    folder_path = os.path.join(OVERLAY_BASE_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder {folder_path} does not exist.")
        return []

    files = []
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if is_supported_file(filename):
                rel_path = os.path.relpath(os.path.join(root, filename), os.path.dirname(os.path.dirname(folder_path)))
                files.append(rel_path.replace("\\", "/"))

    if not files:
        print(f"[ERROR] No media files found in {folder_path}.")
        return []

    if shuffle:
        random.shuffle(files)

    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump(files, f)

    print(f"[BACKGROUND] Playlist created with {len(files)} items from: {folder_name}")
    return files

def create_background_playlist_from_query(query_type, query_content):
    """Create a background playlist based on a user's prompt."""
    selected = select_relevant_folder(query_type, query_content)
    return create_background_playlist_for_folder(selected)

def initialize_background_player():
    """Ensure the background player starts with nothing."""
    ensure_directories_exist()
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump([], f)
    print("[BACKGROUND] Background player initialized with empty playlist.")
    return True

