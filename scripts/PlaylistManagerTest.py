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
current_playlist = []  # Initialize as empty list
current_index = 0  # Track which video is currently playing

# For tracking node transitions in the playlist
node_sequence = []  # Will store the node types for each clip in the playlist

# === Node Configuration ===
# Define all possible states and their transitions
NODES = {
    # Main sitting position (default)
    "main": {
        "loop": "main2main",  # Self loop - sitting idle
        "transitions": {
            "pipe": "main2pipe",         # Transition to pipe
            "newspaper": "main2newspaper", # Transition to newspaper
            "phone": "main2phone",       # Transition to phone
            "standingMansion": "main2standingMansion", # Get up to mansion
            "standingBeach": "main2standingBeach",  # Get up to beach
        }
    },
    # Pipe state
    "pipe": {
        "loop": "pipe2pipe",  # Smoking pipe
        "transitions": {
            "main": "pipe2main"  # Put away pipe, return to main
        }
    },
    # Newspaper state
    "newspaper": {
        "loop": "newspaper2newspaper",  # Reading newspaper
        "transitions": {
            "main": "newspaper2main"  # Put away newspaper, return to main
        }
    },
    # Phone state
    "phone": {
        "loop": "phone2phone",  # Using phone
        "transitions": {
            "main": "phone2main"  # Put away phone, return to main
        }
    },
    # Standing at mansion
    "standingMansion": {
        "loop": "standingMansion2standingMansion",  # Standing idle at mansion
        "transitions": {
            "main": "standingMansion2main",  # Sit back down
            "standingBeach": "standingMansion2standingBeach", # Go to beach
            "standingMansionSmoke": "standingMansion2standingMansionSmoke" # Start smoking
        }
    },
    # Smoking at mansion
    "standingMansionSmoke": {
        "loop": "standingMansionSmoke2standingMansionSmoke",  # Smoking loop
        "transitions": {
            "standingMansion": "standingMansionSmoke2standingMansion"  # Stop smoking
        }
    },
    # Standing at beach
    "standingBeach": {
        "loop": "standingBeach2standingBeach",  # Standing idle at beach
        "transitions": {
            "main": "standingBeach2main",  # Sit back down
            "standingMansion": "standingBeach2standingMansion", # Go to mansion
            "standingBeachSmoke": "standingBeach2standingBeachSmoke" # Start smoking
        }
    },
    # Smoking at beach
    "standingBeachSmoke": {
        "loop": "standingBeachSmoke2standingBeachSmoke",  # Smoking loop
        "transitions": {
            "standingBeach": "standingBeachSmoke2standingBeach"  # Stop smoking
        }
    }
}

# === Transition Probabilities ===
# Defines how likely Darwin is to transition from one state to another
TRANSITION_ODDS = {
    "main": {
        "main": 0.3,        # 50% chance to stay in main loop
        "pipe": 0.1,        # 10% chance to take out pipe
        "newspaper": 0.15,  # 15% chance to take out newspaper
        "phone": 0.1,       # 10% chance to take out phone
        "standingMansion": 0.1, # 10% chance to get up and go to mansion
        "standingBeach": 0.00    # 0% chance to get up and go to beach
    },
    "pipe": {
        "pipe": 0.7,        # 70% chance to keep smoking
        "main": 0.3         # 30% chance to put away pipe
    },
    "newspaper": {
        "newspaper": 0.0,   # 0% chance to keep reading
        "main": 0.0         # 0% chance to put away newspaper
    },
    "phone": {
        "phone": 0.0,       # 0% chance to keep using phone 
        "main": 0.0         # 0% chance to put away phone
    },
    "standingMansion": {
        "standingMansion": 0.5,      # 50% chance to stay standing
        "standingMansionSmoke": 0.0, # 0% chance to start smoking
        "standingBeach": 0.0,        # 0% chance to go to beach
        "main": 0.1                  # 10% chance to sit back down
    },
    "standingMansionSmoke": {
        "standingMansionSmoke": 0.7, # 70% chance to keep smoking
        "standingMansion": 0.3       # 30% chance to stop smoking
    },
    "standingBeach": {
        "standingBeach": 0.5,        # 50% chance to stay at beach
        "standingBeachSmoke": 0.2,   # 20% chance to start smoking
        "standingMansion": 0.2,      # 20% chance to go to mansion
        "main": 0.1                  # 10% chance to sit back down
    },
    "standingBeachSmoke": {
        "standingBeachSmoke": 0.7,   # 70% chance to keep smoking
        "standingBeach": 0.3         # 30% chance to stop smoking
    }
}

# Define supported file extensions
SUPPORTED_EXTENSIONS = [".mp4", ".gif"]

def ensure_directories_exist():
    """Ensure all required directories exist"""
    os.makedirs(PLAYLIST_DIR, exist_ok=True)
    os.makedirs(NODES_DIR, exist_ok=True)
    for node in NODES:
        node_dir = os.path.join(NODES_DIR, NODES[node]["loop"])
        os.makedirs(node_dir, exist_ok=True)
        for transition in NODES[node]["transitions"]:
            transition_dir = os.path.join(NODES_DIR, NODES[node]["transitions"][transition])
            os.makedirs(transition_dir, exist_ok=True)

def is_supported_file(filename):
    """Check if the file has a supported extension"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def get_random_clip_from_node(node_type):
    """Get a random clip from the specified node folder"""
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
    """Choose the next state based on transition probabilities"""
    if current_state not in TRANSITION_ODDS:
        print(f"[ERROR] Unknown state: {current_state}, defaulting to main")
        return "main"
        
    options = list(TRANSITION_ODDS[current_state].keys())
    probabilities = list(TRANSITION_ODDS[current_state].values())
    
    # Sum the probabilities to check if they're valid
    prob_sum = sum(probabilities)
    if prob_sum <= 0:
        print(f"[WARNING] All transition probabilities for {current_state} are zero, defaulting to main")
        return "main"
    
    try:
        return random.choices(options, weights=probabilities, k=1)[0]
    except Exception as e:
        print(f"[ERROR] Failed to choose next state: {e}")
        return "main"  # Default to main if there's an error

def get_transition_clip(from_state, to_state):
    """Get a clip for transitioning between states"""
    if from_state not in NODES or to_state not in NODES[from_state]["transitions"]:
        # If this is an invalid transition, return None
        print(f"[ERROR] Invalid transition from {from_state} to {to_state}")
        return None
        
    transition_type = NODES[from_state]["transitions"][to_state]
    return get_random_clip_from_node(transition_type)

def generate_playlist(num_clips=10):
    """Generate a playlist with the specified number of clips"""
    global current_state, current_playlist, node_sequence
    playlist = []
    node_sequence = []  # Reset node sequence
    
    # Start with a loop clip for the current state
    current_loop = get_random_clip_from_node(NODES[current_state]["loop"])
    if current_loop:
        playlist.append(current_loop)
        node_sequence.append(NODES[current_state]["loop"])
    
    # Generate the rest of the playlist
    for _ in range(num_clips - 1):
        # Choose the next state
        next_state = choose_next_state(current_state)
        
        # If we're staying in the same state, add a loop clip
        if next_state == current_state:
            clip = get_random_clip_from_node(NODES[current_state]["loop"])
            if clip:
                playlist.append(clip)
                node_sequence.append(NODES[current_state]["loop"])
        else:
            # Otherwise, add a transition clip
            transition_node = NODES[current_state]["transitions"][next_state]
            transition_clip = get_random_clip_from_node(transition_node)
            if transition_clip:
                playlist.append(transition_clip)
                node_sequence.append(transition_node)
                
                # Update the current state
                current_state = next_state
                
                # Add a loop clip for the new state
                loop_clip = get_random_clip_from_node(NODES[current_state]["loop"])
                if loop_clip:
                    playlist.append(loop_clip)
                    node_sequence.append(NODES[current_state]["loop"])
    
    # Save the playlist
    with open(PLAYLIST_PATH, "w") as f:
        json.dump(playlist, f)
    
    # Update our internal current_playlist reference
    current_playlist = playlist
    
    # Log the node sequence instead of the full paths
    print(f"[PLAYLIST] New playlist: {node_sequence}")
    print(f"[PLAYLIST] Current state: {current_state}")
    
    return playlist

def idle_playlist_maker():
    """Initial playlist maker that runs on start"""
    global current_state, current_playlist
    ensure_directories_exist()
    
    # Always start from the main state
    current_state = "main"
    print(f"[PLAYLIST] Starting in {current_state} state")
    
    # Generate a playlist starting from main
    playlist = generate_playlist(num_clips=10)
    
    # Make sure current_playlist is set
    current_playlist = playlist
    
    return playlist

def update_video_state(index, current_video):
    """Update the current video index and check if we need a new playlist"""
    global current_index, current_playlist, node_sequence
    
    # Update our tracking
    current_index = int(index)
    
    # Make sure current_playlist is initialized
    if not current_playlist:
        # If for some reason current_playlist is empty, try to load it from file
        try:
            with open(PLAYLIST_PATH, "r") as f:
                current_playlist = json.load(f)
            print(f"[PLAYLIST] Loaded existing playlist")
            # Rebuild node sequence from the paths
            node_sequence = []
            for path in current_playlist:
                if "Nodes/" in path:
                    node_type = path.split("Nodes/")[1].split("/")[0]
                    node_sequence.append(node_type)
                else:
                    node_sequence.append("unknown")
        except Exception as e:
            print(f"[ERROR] Failed to load playlist: {e}")
            # Generate a new playlist if we can't load one
            idle_playlist_maker()
    
    # Log which node is currently playing
    if 0 <= current_index < len(node_sequence):
        current_node = node_sequence[current_index]
        print(f"[PLAYING] Node {current_index}: {current_node}")
    
    # If we're near the end of the playlist (on the 8th item of a 10-item playlist)
    # start preparing a new playlist that continues from the current state
    if current_playlist and current_index >= len(current_playlist) - 3:
        print(f"[PLAYLIST] Near end of playlist (index {current_index}), generating continuation...")
        generate_playlist(num_clips=10)
    
    return True

# Keep these function names for compatibility with existing code
def response_playlist_maker():
    """For compatibility - just calls generate_playlist"""
    return generate_playlist(num_clips=10)

def create_lipsync_playlist():
    """For compatibility - just calls generate_playlist"""
    return generate_playlist(num_clips=10)

# This will ensure current_playlist is initialized if module is loaded directly
if __name__ == "__main__":
    idle_playlist_maker()