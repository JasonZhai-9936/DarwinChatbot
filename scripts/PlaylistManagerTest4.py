import os
import json
import random
import glob

# === Directory Structure ===
PLAYLIST_DIR = os.path.join("stream", "playlist")
os.makedirs(PLAYLIST_DIR, exist_ok=True)
PLAYLIST_PATH = os.path.join(PLAYLIST_DIR, "playlist.json")
NODES_DIR = os.path.join("stream", "Nodes")

# Track our current state and the active playlist
current_state = "main"
current_playlist = []
current_index = 0
node_sequence = []


# === Node Configuration ===
NODES = {
    "main": {
        "loops": ["main2main", "mainSnuff"],
        "transitions": {
            "pipe": "main2pipe",
            "newspaper": "main2newspaper",
            "phone": "main2phone",
            "standingMansion": "main2standingMansion",
            "standingBeach": "main2standingBeach",
        }
    },
    "pipe": {
        "loops": ["pipe2pipe"],
        "transitions": {
            "main": "pipe2main"
        }
    },
    "newspaper": {
        "loops": ["newspaper2newspaper"],
        "transitions": {
            "main": "newspaper2main"
        }
    },
    "phone": {
        "loops": ["phone2phone"],
        "transitions": {
            "main": "phone2main"
        }
    },
    "standingMansion": {
        "loops": ["standingMansion2standingMansion"],
        "transitions": {
            "main": "standingMansion2main",
            "standingBeach": "standingMansion2standingBeach",
            "standingMansionSmoke": "standingMansion2standingMansionSmoke"
        }
    },
    "standingMansionSmoke": {
        "loops": ["standingMansionSmoke2standingMansionSmoke"],
        "transitions": {
            "standingMansion": "standingMansionSmoke2standingMansion"
        }
    },
    "standingBeach": {
        "loops": ["standingBeach2standingBeach"],
        "transitions": {
            "main": "standingBeach2main",
            "standingMansion": "standingBeach2standingMansion",
            "standingBeachSmoke": "standingBeach2standingBeachSmoke"
        }
    },
    "standingBeachSmoke": {
        "loops": ["standingBeachSmoke2standingBeachSmoke"],
        "transitions": {
            "standingBeach": "standingBeach2standingBeach"
        }
    }
}

# === Transition Probabilities (including individual loop odds) ===
TRANSITION_ODDS = {
    "main": {
        "main2main": 0.1,
        "mainSnuff": 0.1,
        "pipe": 0.2,
        "newspaper": 0.2,
        "phone": 0.1,
        "standingMansion": 0.5,
        "standingBeach": 0.2
    },
    "pipe": {
        "pipe2pipe": 0.1,
        "main": 0.6
    },
    "newspaper": {
        "newspaper2newspaper": 0.1,
        "main": 0.5
    },
    "phone": {
        "phone2phone": 0.1,
        "main": 0.5
    },
    "standingMansion": {
        "standingMansion2standingMansion": 0.5,
        "standingMansionSmoke": 0.0,
        "standingBeach": 0.5,
        "main": 0.2
    },
    "standingMansionSmoke": {
        "standingMansionSmoke2standingMansionSmoke": 0.7,
        "standingMansion": 0.3
    },
    "standingBeach": {
        "standingBeach2standingBeach": 0.3,
        "standingBeachSmoke": 0.0,
        "standingMansion": 0.5,
        "main": 0.0
    },
    "standingBeachSmoke": {
        "standingBeachSmoke2standingBeachSmoke": 0.7,
        "standingBeach": 0.3
    }
}
SUPPORTED_EXTENSIONS = [".mp4", ".gif"]

def ensure_directories_exist():
    os.makedirs(PLAYLIST_DIR, exist_ok=True)
    os.makedirs(NODES_DIR, exist_ok=True)
    for node in NODES:
        for loop in NODES[node].get("loops", []):
            os.makedirs(os.path.join(NODES_DIR, loop), exist_ok=True)
        for transition in NODES[node]["transitions"].values():
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
        print(f"[ERROR] Unknown state: {current_state}, defaulting to main")
        return "main"
    options = list(TRANSITION_ODDS[current_state].keys())
    probabilities = list(TRANSITION_ODDS[current_state].values())
    if sum(probabilities) <= 0:
        print(f"[WARNING] All transition probabilities for {current_state} are zero, defaulting to main")
        return "main"
    return random.choices(options, weights=probabilities, k=1)[0]

def generate_playlist(num_clips=10):
    global current_state, current_playlist, node_sequence
    playlist = []
    node_sequence = []

    # Initial loop clip from loop pool with weights
    loop_choices = NODES[current_state]["loops"]
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
            loop_choices = NODES[current_state]["loops"]
            loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in loop_choices]
            if sum(loop_weights) > 0:
                selected_loop = random.choices(loop_choices, weights=loop_weights, k=1)[0]
                clip = get_random_clip_from_node(selected_loop)
                if clip:
                    playlist.append(clip)
                    node_sequence.append(selected_loop)
        else:
            transition_node = NODES[current_state]["transitions"].get(next_state)
            if not transition_node:
                continue
            transition_clip = get_random_clip_from_node(transition_node)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_node)
                current_state = next_state

                # Add next state's loop
                new_loop_choices = NODES[current_state]["loops"]
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

def idle_playlist_maker():
    global current_state, current_playlist
    ensure_directories_exist()
    current_state = "main"
    print(f"[PLAYLIST] Starting in {current_state} state")
    playlist = generate_playlist(num_clips=20)
    current_playlist = playlist
    return playlist

def update_video_state(index, current_video):
    global current_index, current_playlist, node_sequence, current_state
    
    old_state = current_state  # FIXED: Define old_state before using it
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
                    # Handle lipsync files too
                    node_type = path.split("lipsync_responses/")[1].split("/")[0]
                    node_sequence.append(node_type)
                else:
                    node_sequence.append("unknown")
        except Exception as e:
            print(f"[ERROR] Failed to load playlist: {e}")
            idle_playlist_maker()
    
    # UPDATE: Also update current_state based on the current video
    if 0 <= current_index < len(node_sequence):
        current_node = node_sequence[current_index]
        print(f"[PLAYING] Node {current_index}: {current_node}")
        
        # Determine what state we're in based on the node type
        if current_node.startswith("main"):
            current_state = "main"
        elif current_node.startswith("pipe"):
            current_state = "pipe"
        elif current_node.startswith("newspaper"):
            current_state = "newspaper"
        elif current_node.startswith("phone"):
            current_state = "phone"
        elif current_node.startswith("standingMansionSmoke"):
            current_state = "standingMansionSmoke"
        elif current_node.startswith("standingMansion"):
            current_state = "standingMansion"
        elif current_node.startswith("standingBeachSmoke"):
            current_state = "standingBeachSmoke"
        elif current_node.startswith("standingBeach"):
            current_state = "standingBeach"
        
        print(f"[DEBUG] Node {current_index}: {current_node}, old_state={old_state}, new_state={current_state}")
        print(f"[STATE] Updated current_state to: {current_state}")
    
    if current_playlist and current_index >= len(current_playlist) - 3:
        print(f"[PLAYLIST] Near end of playlist (index {current_index}), generating continuation...")
        generate_playlist(num_clips=10)
    return True

def response_playlist_maker():
    return generate_playlist(num_clips=10)

def create_lipsync_playlist():
    return generate_playlist(num_clips=10)

def make_response_playlist_with_lipsync():
    """
    Create a lipsync response playlist using the ACTUAL current node that's playing
    """
    global current_state, current_playlist, node_sequence, current_index

    # Get the ACTUAL current node that's playing (ground truth)
    if 0 <= current_index < len(node_sequence):
        current_node = node_sequence[current_index]
        print(f"[PLAYLIST] Creating lipsync from ACTUAL current node: {current_node} (index: {current_index})")
    else:
        print(f"[ERROR] Invalid current_index {current_index}, defaulting to main")
        current_node = "main2main"

    # Determine target based on the ACTUAL current node, not current_state
    if current_node.startswith("standingMansion"):
        target_node = "standingMansion"
        node_folder = "standingMansion2standingMansion"
    elif current_node.startswith("standingBeach"):
        target_node = "standingBeach"
        node_folder = "standingBeach2standingBeach"
    else:
        # For main, pipe, newspaper, phone nodes - all go to main for talking
        target_node = "main"
        node_folder = "main2main"

    print(f"[DEBUG] Current node: {current_node}")
    print(f"[DEBUG] Determined lipsync node folder: {node_folder} (target node: {target_node})")

    lipsync_dir = os.path.join("stream", "lipsync_responses", node_folder)
    if not os.path.exists(lipsync_dir):
        print(f"[ERROR] No lipsync directory for node {node_folder}")
        print(f"[ERROR] Expected directory: {lipsync_dir}")
        return []

    lipsync_files = [f for f in os.listdir(lipsync_dir) if is_supported_file(f)]
    if not lipsync_files:
        print(f"[ERROR] No lipsync video files found in {lipsync_dir}")
        return []

    lipsync_clip = os.path.join("lipsync_responses", node_folder, random.choice(lipsync_files)).replace("\\", "/")

    playlist = []
    node_sequence = []

    # Determine the current state from the current node for transition logic
    if current_node.startswith("standingMansionSmoke"):
        current_state_for_transition = "standingMansionSmoke"
    elif current_node.startswith("standingMansion"):
        current_state_for_transition = "standingMansion"
    elif current_node.startswith("standingBeachSmoke"):
        current_state_for_transition = "standingBeachSmoke"
    elif current_node.startswith("standingBeach"):
        current_state_for_transition = "standingBeach"
    elif current_node.startswith("pipe"):
        current_state_for_transition = "pipe"
    elif current_node.startswith("newspaper"):
        current_state_for_transition = "newspaper"
    elif current_node.startswith("phone"):
        current_state_for_transition = "phone"
    else:
        current_state_for_transition = "main"

    print(f"[DEBUG] Derived current state for transitions: {current_state_for_transition}")

    # Add transition TO the target node if not already in that node
    if current_state_for_transition != target_node:
        print(f"[DEBUG] Need to transition from {current_state_for_transition} to {target_node}")
        transition_folder = NODES[current_state_for_transition]["transitions"].get(target_node)
        if transition_folder:
            transition_clip = get_random_clip_from_node(transition_folder)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_folder)
                current_state = target_node  # Update global state
                print(f"[DEBUG] Added transition: {transition_folder}")
        else:
            print(f"[ERROR] No transition from {current_state_for_transition} to {target_node}")
    else:
        print(f"[DEBUG] Already in target node {target_node}, no transition needed")
        current_state = target_node  # Make sure global state is correct

    # Add lipsync response clip
    playlist.append(lipsync_clip)
    node_sequence.append(node_folder)
    print(f"[DEBUG] Added lipsync clip: {lipsync_clip}")

    # === Add more clips just like idle_playlist_maker does ===
    for _ in range(10):  # standard continuation
        next_state = choose_next_state(current_state)
        if next_state == current_state:
            loop_choices = NODES[current_state]["loops"]
            loop_weights = [TRANSITION_ODDS[current_state].get(loop, 0) for loop in loop_choices]
            if sum(loop_weights) > 0:
                selected_loop = random.choices(loop_choices, weights=loop_weights, k=1)[0]
                clip = get_random_clip_from_node(selected_loop)
                if clip:
                    playlist.append(clip)
                    node_sequence.append(selected_loop)
        else:
            transition_node = NODES[current_state]["transitions"].get(next_state)
            if not transition_node:
                continue
            transition_clip = get_random_clip_from_node(transition_node)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_node)
                current_state = next_state
                loop_choices = NODES[current_state]["loops"]
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

def load_custom_playlist(custom_path):
    global current_playlist, node_sequence
    if not os.path.exists(custom_path):
        print(f"[ERROR] Custom playlist file not found: {custom_path}")
        return False

    try:
        with open(custom_path, "r") as f:
            playlist_data = json.load(f)

        with open(PLAYLIST_PATH, "w") as f:
            json.dump(playlist_data, f)

        current_playlist = playlist_data
        node_sequence = []
        for path in playlist_data:
            if "Nodes/" in path:
                node_type = path.split("Nodes/")[1].split("/")[0]
                node_sequence.append(node_type)
            else:
                node_sequence.append("unknown")

        print(f"[PLAYLIST] Loaded custom playlist from {custom_path}")
        print(f"[PLAYLIST] Node sequence: {node_sequence}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to load custom playlist: {e}")
        return False

def load_scripted_playlist():
    script_path = os.path.join(PLAYLIST_DIR, "script.json")
    if os.path.exists(script_path):
        print("[PLAYLIST] Detected scripted playlist, loading script.json...")
        return load_custom_playlist(script_path)
    print("[PLAYLIST] No scripted playlist found.")
    return False

if __name__ == "__main__":
    idle_playlist_maker()