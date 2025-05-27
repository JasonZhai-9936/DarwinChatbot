import os
import random
import json
import glob
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

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

def select_background_folder_with_llm(query_type, user_input, available_folders, llm_instance):
    """
    Have the LLM directly select the best folder based on the query
    """
    from langchain_core.messages import SystemMessage
    
    if query_type == 1:
        print(f"{Fore.MAGENTA}[BACKGROUND] Generic non-Darwin question - No specific background needed{Style.RESET_ALL}")
        return None
        
    if not available_folders:
        print(f"{Fore.RED}[BACKGROUND] No available folders to select from{Style.RESET_ALL}")
        return None
        
    # Get the LLM to choose the most appropriate folder
    folder_descriptions = {
        "beagle voyage": "Content related to Darwin's journey on HMS Beagle, his travels, explorations, and discoveries during the voyage, especially in Galapagos.",
        "darwin_family": "Content about Darwin's family life, including his wife Emma, children, parents, and other family members.",
        "darwin_himself": "Personal content about Darwin himself, including portraits, biographical details, and personal history.",
        "darwins finches": "Content specifically about Darwin's famous finches from the Galapagos Islands and their role in his theory development.",
        "evolution_conv_div": "Content about evolutionary concepts of convergence and divergence, species adaptation and diversification.",
        "natural_selection": "Content related to natural selection, Darwin's primary mechanism for evolution, survival of the fittest, adaptation.",
        "shropshire": "Content about Darwin's birthplace and childhood in Shropshire, England, including his early years and education.",
        "tree_of_life": "Content related to Darwin's concept of the tree of life, showing relationships between species and common ancestry."
    }
    
    # Build a description of only the available folders
    available_descriptions = []
    for folder in available_folders:
        folder_lower = folder.lower()
        if folder_lower in folder_descriptions:
            available_descriptions.append(f"{folder}: {folder_descriptions[folder_lower]}")
        else:
            available_descriptions.append(f"{folder}: Content related to {folder.replace('_', ' ')}")
    
    folder_info = "\n".join(available_descriptions)
            
    prompt = [
        SystemMessage(content=(
            f"You are helping select the most appropriate visual content to display for a Darwin chatbot.\n\n"
            f"Based on the user's query, choose the SINGLE most relevant folder from the options below. "
            f"The selected folder will display images/videos related to that aspect of Darwin's life or work.\n\n"
            f"Available folders and their content:\n{folder_info}\n\n"
            f"User query: {user_input}\n\n"
            f"Analyze the query and return ONLY the exact name of the single most appropriate folder from the list. "
            f"Return just the folder name, nothing else. If no folder is clearly relevant, return the name of the "
            f"folder that contains general Darwin content."
        )),
    ]
    
    try:
        response = llm_instance.invoke(prompt).content.strip()
        print(f"{Fore.MAGENTA}[BACKGROUND] LLM selected folder: {response}{Style.RESET_ALL}")
        
        # Check if the response is a valid folder
        for folder in available_folders:
            if folder.lower() == response.lower() or folder == response:
                print(f"{Fore.GREEN}[BACKGROUND] Found matching folder: {folder}{Style.RESET_ALL}")
                return folder
                
        # If no exact match, check if any part of the response matches a folder
        for folder in available_folders:
            if folder.lower() in response.lower():
                print(f"{Fore.YELLOW}[BACKGROUND] Found partial match in LLM response: {folder}{Style.RESET_ALL}")
                return folder
        
        # If still no match, return a random folder
        print(f"{Fore.RED}[BACKGROUND] No matching folder found in LLM response: '{response}'{Style.RESET_ALL}")
        return random.choice(available_folders)
        
    except Exception as e:
        print(f"{Fore.RED}[BACKGROUND] Error getting folder selection from LLM: {e}{Style.RESET_ALL}")
        # Fallback to random selection
        return random.choice(available_folders)

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

def create_background_playlist_from_query_with_llm(query_type, query_content, llm_instance):
    """Create a background playlist based on a user's prompt using LLM selection."""
    available_folders = get_available_folders()
    selected = select_background_folder_with_llm(query_type, query_content, available_folders, llm_instance)
    return create_background_playlist_for_folder(selected)

def initialize_background_player():
    """Ensure the background player starts with nothing."""
    ensure_directories_exist()
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump([], f)
    print("[BACKGROUND] Background player initialized with empty playlist.")
    return True

def create_background_playlist(num_clips=10):
    """For backward compatibility with existing code"""
    # Just pick a random folder for this function
    available_folders = get_available_folders()
    if not available_folders:
        return []
    
    selected_folder = random.choice(available_folders)
    return create_background_playlist_for_folder(selected_folder)