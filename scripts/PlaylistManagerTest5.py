import os
import json
import random
import glob

# === Load Configuration ===
CONFIG_PATH = os.path.join("stream", "playlist", "nodes.json")

def load_node_config():
    """Load the node configuration from JSON file"""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load node config: {e}")
        return None

# Load configuration at startup
NODE_CONFIG = load_node_config()

if not NODE_CONFIG:
    raise Exception("Failed to load node configuration - system cannot start")

# Extract configuration sections
NODES = NODE_CONFIG["nodes"]
TRANSITION_ODDS = NODE_CONFIG["transition_probabilities"]
TALKING_NODES = NODE_CONFIG["talking_nodes"]
NODE_HIERARCHY = NODE_CONFIG["node_hierarchy"]
SETTINGS = NODE_CONFIG["settings"]

# === Directory Structure ===
PLAYLIST_DIR = os.path.join("stream", "playlist")
os.makedirs(PLAYLIST_DIR, exist_ok=True)
PLAYLIST_PATH = os.path.join(PLAYLIST_DIR, "playlist.json")
NODES_DIR = os.path.join("stream", "Nodes")

# Track our current state and the active playlist
current_state = SETTINGS["default_start_node"]
current_playlist = []
current_index = 0
node_sequence = []

SUPPORTED_EXTENSIONS = SETTINGS["supported_extensions"]

def get_current_node_from_name(node_name):
    """Determine which node we're currently in based on the node name"""
    for node_key, node_data in NODES.items():
        # Check if this node name starts with any of the node's loop or transition names
        for loop in node_data.get("loops", []):
            if node_name.startswith(loop.split("2")[0]):
                return node_key
        for transition in node_data.get("transitions", {}).values():
            if node_name.startswith(transition.split("2")[0]):
                return node_key
    
    # Fallback: check if node_name directly starts with a node key
    for node_key in NODES.keys():
        if node_name.startswith(node_key):
            return node_key
    
    return SETTINGS["default_start_node"]

def get_talking_node_for_current_state(current_node_key):
    """Get the appropriate talking node for the current state"""
    if current_node_key in NODES:
        return NODES[current_node_key]["talking_node"]
    return SETTINGS["default_start_node"]

def get_transition_path_to_talking_node(from_node, to_talking_node):
    """Get the sequence of transitions needed to reach a talking node"""
    if to_talking_node in TALKING_NODES:
        transition_paths = TALKING_NODES[to_talking_node]["transition_paths"]
        return transition_paths.get(from_node, [])
    return []

def ensure_directories_exist():
    os.makedirs(PLAYLIST_DIR, exist_ok=True)
    os.makedirs(NODES_DIR, exist_ok=True)
    
    # Create directories for all node types defined in config
    for node_data in NODES.values():
        for loop in node_data.get("loops", []):
            os.makedirs(os.path.join(NODES_DIR, loop), exist_ok=True)
        for transition in node_data["transitions"].values():
            os.makedirs(os.path.join(NODES_DIR, transition), exist_ok=True)

def is_supported_file(filename):
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def get_random_clip_from_node(node_type):
    node_dir = os.path.join(NODES_DIR, node_type)
    if not os.path.exists(node_dir):
        print(f"[ERROR] Node directory {node_dir} does not exist.")
        return None
    files = [f for f in os.listdir(node_dir) if is_supported_file(f)]
    if not files:
        print(f"[ERROR] No video files found in {node_dir}.")
        return None
    selected_file = random.choice(files)
    return os.path.join("Nodes", node_type, selected_file).replace("\\", "/")

def choose_next_state(current_state):
    if current_state not in TRANSITION_ODDS:
        print(f"[ERROR] Unknown state: {current_state}, defaulting to {SETTINGS['default_start_node']}")
        return SETTINGS["default_start_node"]
    
    options = list(TRANSITION_ODDS[current_state].keys())
    probabilities = list(TRANSITION_ODDS[current_state].values())
    
    if sum(probabilities) <= 0:
        print(f"[WARNING] All transition probabilities for {current_state} are zero, defaulting to {SETTINGS['default_start_node']}")
        return SETTINGS["default_start_node"]
    
    return random.choices(options, weights=probabilities, k=1)[0]

def generate_playlist(num_clips=None):
    global current_state, current_playlist, node_sequence
    
    if num_clips is None:
        num_clips = SETTINGS["default_playlist_length"]
    
    playlist = []
    node_sequence = []

    # Initial loop clip from current state
    current_node_data = NODES[current_state]
    loop_choices = current_node_data["loops"]
    loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in loop_choices]
    
    if sum(loop_weights) > 0:
        selected_loop = random.choices(loop_choices, weights=loop_weights, k=1)[0]
        loop_clip = get_random_clip_from_node(selected_loop)
        if loop_clip:
            playlist.append(loop_clip)
            node_sequence.append(selected_loop)

    for _ in range(num_clips - 1):
        next_state = choose_next_state(current_state)
        if next_state == current_state:
            # Stay in same state, play loop
            current_node_data = NODES[current_state]
            loop_choices = current_node_data["loops"]
            loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in loop_choices]
            if sum(loop_weights) > 0:
                selected_loop = random.choices(loop_choices, weights=loop_weights, k=1)[0]
                clip = get_random_clip_from_node(selected_loop)
                if clip:
                    playlist.append(clip)
                    node_sequence.append(selected_loop)
        else:
            # Transition to new state
            current_node_data = NODES[current_state]
            transition_node = current_node_data["transitions"].get(next_state)
            if not transition_node:
                continue
            
            transition_clip = get_random_clip_from_node(transition_node)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_node)
                current_state = next_state

                # Add next state's loop
                new_node_data = NODES[current_state]
                new_loop_choices = new_node_data["loops"]
                new_loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in new_loop_choices]
                if sum(new_loop_weights) > 0:
                    selected_loop = random.choices(new_loop_choices, weights=new_loop_weights, k=1)[0]
                    loop_clip = get_random_clip_from_node(selected_loop)
                    if loop_clip:
                        playlist.append(loop_clip)
                        node_sequence.append(selected_loop)

    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)
    current_playlist = playlist
    print(f"[PLAYLIST] New playlist: {node_sequence}")
    print(f"[PLAYLIST] Current state: {current_state}")
    return playlist

def update_video_state(index, current_video):
    global current_index, current_playlist, node_sequence, current_state
    
    old_state = current_state
    current_index = int(index)

    print(f"[DEBUG] update_video_state called with index={index}, current_state before={old_state}")

    if not current_playlist:
        try:
            with open(PLAYLIST_PATH, "r") as f:
                current_playlist = json.load(f)
            node_sequence = []
            for path in current_playlist:
                if "Nodes/" in path:
                    node_type = path.split("Nodes/")[1].split("/")[0]
                    node_sequence.append(node_type)
                elif "lipsync_responses/" in path:
                    node_type = path.split("lipsync_responses/")[1].split("/")[0]
                    node_sequence.append(node_type)
                else:
                    node_sequence.append("unknown")
        except Exception as e:
            print(f"[ERROR] Failed to load playlist: {e}")
            idle_playlist_maker()
    
    # Update current_state based on the current video using config
    if 0 <= current_index < len(node_sequence):
        current_node = node_sequence[current_index]
        print(f"[PLAYING] Node {current_index}: {current_node}")
        
        # Use config to determine current state
        current_state = get_current_node_from_name(current_node)
        
        print(f"[DEBUG] Node {current_index}: {current_node}, old_state={old_state}, new_state={current_state}")
        print(f"[STATE] Updated current_state to: {current_state}")
    
    if current_playlist and current_index >= len(current_playlist) - 3:
        print(f"[PLAYLIST] Near end of playlist (index {current_index}), generating continuation...")
        generate_playlist()
    return True

def make_response_playlist_with_lipsync():
    """Create a lipsync response playlist using the JSON configuration"""
    global current_state, current_playlist, node_sequence, current_index

    # Get the ACTUAL current node that's playing
    if 0 <= current_index < len(node_sequence):
        current_node = node_sequence[current_index]
        print(f"[PLAYLIST] Creating lipsync from ACTUAL current node: {current_node} (index: {current_index})")
    else:
        print(f"[ERROR] Invalid current_index {current_index}, defaulting to {SETTINGS['default_start_node']}")
        current_node = f"{SETTINGS['default_start_node']}2{SETTINGS['default_start_node']}"

    # Determine current state from node name using config
    current_node_key = get_current_node_from_name(current_node)
    
    # Get the talking node for this state
    target_talking_node = get_talking_node_for_current_state(current_node_key)
    
    print(f"[DEBUG] Current node: {current_node}")
    print(f"[DEBUG] Current node key: {current_node_key}")
    print(f"[DEBUG] Target talking node: {target_talking_node}")

    # Get transition path to talking node
    transition_path = get_transition_path_to_talking_node(current_node_key, target_talking_node)
    
    playlist = []
    node_sequence = []

    # Add transition clips to reach talking node
    for transition_name in transition_path:
        transition_clip = get_random_clip_from_node(transition_name)
        if transition_clip:
            playlist.append(transition_clip)
            node_sequence.append(transition_name)
            print(f"[DEBUG] Added transition: {transition_name}")

    # Update current state to talking node
    current_state = target_talking_node

    # Add lipsync response clip
    talking_node_data = TALKING_NODES[target_talking_node]
    lipsync_folder = talking_node_data["lipsync_folder"]
    
    lipsync_dir = os.path.join("stream", SETTINGS["lipsync_base_path"], lipsync_folder)
    if not os.path.exists(lipsync_dir):
        print(f"[ERROR] No lipsync directory for node {lipsync_folder}")
        print(f"[ERROR] Expected directory: {lipsync_dir}")
        return []

    lipsync_files = [f for f in os.listdir(lipsync_dir) if is_supported_file(f)]
    if not lipsync_files:
        print(f"[ERROR] No lipsync video files found in {lipsync_dir}")
        return []

    lipsync_clip = os.path.join(SETTINGS["lipsync_base_path"], lipsync_folder, random.choice(lipsync_files)).replace("\\", "/")
    playlist.append(lipsync_clip)
    node_sequence.append(lipsync_folder)
    print(f"[DEBUG] Added lipsync clip: {lipsync_clip}")

    # Continue with standard playlist generation
    for _ in range(SETTINGS["default_playlist_length"]):
        next_state = choose_next_state(current_state)
        if next_state == current_state:
            current_node_data = NODES[current_state]
            loop_choices = current_node_data["loops"]
            loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in loop_choices]
            if sum(loop_weights) > 0:
                selected_loop = random.choices(loop_choices, weights=loop_weights, k=1)[0]
                clip = get_random_clip_from_node(selected_loop)
                if clip:
                    playlist.append(clip)
                    node_sequence.append(selected_loop)
        else:
            current_node_data = NODES[current_state]
            transition_node = current_node_data["transitions"].get(next_state)
            if not transition_node:
                continue
            transition_clip = get_random_clip_from_node(transition_node)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_node)
                current_state = next_state
                
                new_node_data = NODES[current_state]
                loop_choices = new_node_data["loops"]
                loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in loop_choices]
                if sum(loop_weights) > 0:
                    selected_loop = random.choices(loop_choices, weights=loop_weights, k=1)[0]
                    loop_clip = get_random_clip_from_node(selected_loop)
                    if loop_clip:
                        playlist.append(loop_clip)
                        node_sequence.append(selected_loop)

    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)

    current_playlist = playlist
    print(f"[PLAYLIST] Full response playlist: {node_sequence}")
    return playlist

def idle_playlist_maker():
    global current_state, current_playlist
    ensure_directories_exist()
    current_state = SETTINGS["default_start_node"]
    print(f"[PLAYLIST] Starting in {current_state} state")
    playlist = generate_playlist(num_clips=20)
    current_playlist = playlist
    return playlist

# Keep other functions for backward compatibility
def response_playlist_maker():
    return generate_playlist()

def create_lipsync_playlist():
    return generate_playlist()

if __name__ == "__main__":
    idle_playlist_maker()