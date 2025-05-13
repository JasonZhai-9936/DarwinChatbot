import os
import random
import json
import glob
import time

# Define directory structure
OVERLAY_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream", "Overlay_Assets")
BACKGROUND_PLAYLIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream", "playlist")
BACKGROUND_PLAYLIST_PATH = os.path.join(BACKGROUND_PLAYLIST_DIR, "background_playlist.json")

# Supported video and image extensions
SUPPORTED_EXTENSIONS = [".mp4", ".png", ".jpg", ".jpeg", ".webp", ".gif"]

def ensure_directories_exist():
    """Ensure all required directories exist"""
    os.makedirs(BACKGROUND_PLAYLIST_DIR, exist_ok=True)

def is_supported_file(filename):
    """Check if the file has a supported extension"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def get_available_folders():
    """Get list of available folders in the Overlay_Assets directory"""
    if not os.path.exists(OVERLAY_BASE_DIR):
        print(f"[ERROR] Overlay base directory {OVERLAY_BASE_DIR} does not exist.")
        return []
    
    folders = [f for f in os.listdir(OVERLAY_BASE_DIR) if os.path.isdir(os.path.join(OVERLAY_BASE_DIR, f))]
    print(f"[BACKGROUND] Available folders: {folders}")
    return folders

def select_relevant_folder(query_type, query_content):
    """
    Select a relevant folder based on query type and content
    
    Args:
        query_type (int): Type of query (1, 2, or 3)
        query_content (str): User's query text
        
    Returns:
        str: Selected folder name or None if no relevant folder
    """
    # If not Darwin-related, don't show any specific background
    if query_type == 1:
        print("[BACKGROUND] Query not Darwin-related, no specific background needed")
        return None
    
    available_folders = get_available_folders()
    if not available_folders:
        print("[BACKGROUND] No folders available")
        return None
    
    # Convert query to lowercase for case-insensitive matching
    query_lower = query_content.lower()
    
    # Keywords mapping to folders
    folder_keywords = {
        "beagle voyage": ["beagle", "beagle voyage", "galapagos"],
        "darwin_family": ["family", "childhood", "wife", "children", "marriage", "emma"],
        "darwin_himself": [ "portrait", "life", "autobiography"],
        "darwins finches": ["finch", "finches", "bird", "beak"],
        "evolution_conv_div": ["evolution", "divergence", "convergence", "species", "adaptation", "diversification"],
        "natural_selection": ["natural selection", "survival", "fittest", "adaptation", "struggle", "competition"],
        "shropshire": ["shropshire", "childhood", "england", "home", "shrewsbury", "birthplace","born"],
        "tree_of_life": ["tree of life"]
    }
    
    # Score each folder based on keyword matches
    folder_scores = {folder: 0 for folder in available_folders}
    
    for folder, keywords in folder_keywords.items():
        if folder in available_folders:
            for keyword in keywords:
                if keyword in query_lower:
                    folder_scores[folder] += 1
    
    # Get the folder with the highest score
    max_score = max(folder_scores.values()) if folder_scores else 0
    if max_score > 0:
        best_folders = [folder for folder, score in folder_scores.items() if score == max_score]
        selected_folder = random.choice(best_folders)
        print(f"[BACKGROUND] Selected folder: {selected_folder} with score {max_score}")
        return selected_folder
    
    # If no matches, choose a random folder if it's Darwin-related (types 2 or 3)
    if query_type in [2, 3]:
        selected_folder = random.choice(available_folders)
        print(f"[BACKGROUND] No specific match found, randomly selected: {selected_folder}")
        return selected_folder
    
    return None

def create_background_playlist_for_folder(folder_name, shuffle=True):
    """
    Create a background playlist from files in the specified folder
    
    Args:
        folder_name (str): Name of the folder to use
        shuffle (bool): Whether to shuffle the files
        
    Returns:
        list: List of file paths for the playlist
    """
    ensure_directories_exist()
    
    if not folder_name:
        print("[BACKGROUND] No folder specified, creating empty playlist")
        with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
            json.dump([], f)
        return []
    
    folder_path = os.path.join(OVERLAY_BASE_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder {folder_path} does not exist.")
        return []
    
    # Get all supported media files in the folder
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            if is_supported_file(filename):
                rel_path = os.path.relpath(os.path.join(root, filename), os.path.dirname(os.path.dirname(folder_path)))
                rel_path = rel_path.replace("\\", "/")
                files.append(rel_path)
    
    if not files:
        print(f"[ERROR] No media files found in {folder_path}.")
        return []
    
    # Shuffle if requested
    if shuffle:
        random.shuffle(files)
    
    # Save playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump(files, f)
    
    print(f"[BACKGROUND] New background playlist created with {len(files)} items from {folder_name}")
    return files

def create_background_playlist_from_query(query_type, query_content):
    """
    Create a background playlist based on the query type and content
    
    Args:
        query_type (int): Type of query (1, 2, or 3)
        query_content (str): User's query text
        
    Returns:
        list: List of file paths for the playlist
    """
    selected_folder = select_relevant_folder(query_type, query_content)
    return create_background_playlist_for_folder(selected_folder)

def initialize_background_player():
    """Initialize the background player with a delay"""
    # Start with an empty playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump([], f)

    def delayed_playlist_creation():
        time.sleep(3)  # Delay before generating playlist
        first_folder = next(iter(get_available_folders()), None)
        if first_folder:
            create_background_playlist_for_folder(first_folder)
            print(f"[BACKGROUND] Background media now playing from {first_folder} after delay")

    import threading
    bg_thread = threading.Thread(target=delayed_playlist_creation)
    bg_thread.daemon = True
    bg_thread.start()

    return True