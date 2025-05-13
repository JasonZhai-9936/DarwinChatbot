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
            "standingBeach": "standingBeachSmoke2standingBeach"
        }
    }
}

# === Transition Probabilities ===
TRANSITION_ODDS = {
    "main": {
        "main": 0.3,
        "pipe": 0.1,
        "newspaper": 0.15,
        "phone": 0.1,
        "standingMansion": 0.1,
        "standingBeach": 0.00
    },
    "pipe": {
        "pipe": 0.7,
        "main": 0.3
    },
    "newspaper": {
        "newspaper": 0.0,
        "main": 0.0
    },
    "phone": {
        "phone": 0.0,
        "main": 0.0
    },
    "standingMansion": {
        "standingMansion": 0.5,
        "standingMansionSmoke": 0.0,
        "standingBeach": 0.0,
        "main": 0.1
    },
    "standingMansionSmoke": {
        "standingMansionSmoke": 0.7,
        "standingMansion": 0.3
    },
    "standingBeach": {
        "standingBeach": 0.5,
        "standingBeachSmoke": 0.2,
        "standingMansion": 0.2,
        "main": 0.1
    },
    "standingBeachSmoke": {
        "standingBeachSmoke": 0.7,
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

    # Initial loop clip
    selected_loop = random.choice(NODES[current_state]["loops"])
    loop_clip = get_random_clip_from_node(selected_loop)
    if loop_clip:
        playlist.append(loop_clip)
        node_sequence.append(selected_loop)

    for _ in range(num_clips - 1):
        next_state = choose_next_state(current_state)
        if next_state == current_state:
            selected_loop = random.choice(NODES[current_state]["loops"])
            clip = get_random_clip_from_node(selected_loop)
            if clip:
                playlist.append(clip)
                node_sequence.append(selected_loop)
        else:
            transition_node = NODES[current_state]["transitions"][next_state]
            transition_clip = get_random_clip_from_node(transition_node)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_node)
                current_state = next_state
                selected_loop = random.choice(NODES[current_state]["loops"])
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
    playlist = generate_playlist(num_clips=10)
    current_playlist = playlist
    return playlist

def update_video_state(index, current_video):
    global current_index, current_playlist, node_sequence
    current_index = int(index)
    if not current_playlist:
        try:
            with open(PLAYLIST_PATH, "r") as f:
                current_playlist = json.load(f)
            node_sequence = []
            for path in current_playlist:
                if "Nodes/" in path:
                    node_type = path.split("Nodes/")[1].split("/")[0]
                    node_sequence.append(node_type)
                else:
                    node_sequence.append("unknown")
        except Exception as e:
            print(f"[ERROR] Failed to load playlist: {e}")
            idle_playlist_maker()
    if 0 <= current_index < len(node_sequence):
        print(f"[PLAYING] Node {current_index}: {node_sequence[current_index]}")
    if current_playlist and current_index >= len(current_playlist) - 3:
        print(f"[PLAYLIST] Near end of playlist (index {current_index}), generating continuation...")
        generate_playlist(num_clips=10)
    return True

def response_playlist_maker():
    return generate_playlist(num_clips=10)

def create_lipsync_playlist():
    return generate_playlist(num_clips=10)

if __name__ == "__main__":
    idle_playlist_maker()
