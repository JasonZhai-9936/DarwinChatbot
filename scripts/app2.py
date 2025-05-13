# app.py

import threading
import time
import os, json
import glob
import atexit
from nicegui import ui, app
import random

# Import LLM function - uncomment this line to use the LLM
from LLM_Groq import generate_darwin_response
from PlaylistManagerTest import idle_playlist_maker, response_playlist_maker, create_lipsync_playlist
from BackgroundManager import initialize_background_player, create_background_playlist
from uiTest import build_ui  # Import build_ui from the ui.py file

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")
STREAM_SPEECH_DIR = os.path.join(REPO_DIR, "stream", "speech")
PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")

# === Thread management ===
_main_thread = None
_thread_lock = threading.Lock()
_shutdown_flag = False

# === State Flags ===
awaiting_response = False
user_prompt = ""  # Store the user's prompt
llm_response = ""  # Store the LLM's response

# Expose media folder
app.add_static_files('/stream', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stream')))

def get_latest_video_from_live_dir():
    """Get the most recent video from the live directory"""
    video_files = glob.glob(os.path.join(STREAM_LIVE_DIR, "*.mp4"))
    if not video_files:
        return None
    return max(video_files, key=os.path.getctime)

def update_playlist_with_single_video(video_path):
    """Create a playlist with just the specified video"""
    # Convert absolute path to relative path for playlist
    try:
        # Get the path relative to the REPO_DIR
        relative_path = os.path.relpath(video_path, os.path.join(REPO_DIR))
        
        # Important fix: Remove any "stream" prefix to avoid path duplication
        if relative_path.startswith("stream\\") or relative_path.startswith("stream/"):
            relative_path = relative_path[7:]  # Skip past "stream/" or "stream\"
        
        # Convert backslashes to forward slashes for web paths
        web_path = relative_path.replace("\\", "/")
        
        # Create a playlist with just this video
        playlist = [web_path]
        
        # Save the playlist
        with open(PLAYLIST_PATH, "w") as f:
            json.dump(playlist, f)
        
        print(f"[PLAYLIST] Updated playlist with single video: {web_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update playlist: {e}")
        return False

def idle_mode():
    print("[MAIN] Starting idle mode...")
    # Generate a new playlist based on node transitions
    idle_playlist_maker()

    print("[MAIN] Idle mode finished, waiting for response trigger...")
    return

def response_mode():
    global user_prompt, llm_response
    print("[MAIN] Starting response mode...")
    
    # Get LLM response using the imported function
    try:
        print(f"[LLM] Processing user prompt: {user_prompt[:50]}...")
        
        # Call the LLM to generate a response
        llm_response = generate_darwin_response(user_prompt)
        
        print(f"[LLM] Response generated: {llm_response[:100]}...")
        
        # Log the full response to the console
        print("[LLM] FULL RESPONSE:")
        print("=============================")
        print(llm_response)
        print("=============================")
    except Exception as e:
        print(f"[ERROR] Failed to generate LLM response: {e}")
        llm_response = "I beg your pardon, but I seem to be experiencing some difficulty in processing your query at the moment."
    
    # Generate a response playlist
    response_playlist_maker()
    
    # Update background playlist during response (smaller number of clips for circular display)
    create_background_playlist(num_clips=10)
    
    success = True
    
    # Reset the user prompt for next interaction
    user_prompt = ""
    
    return success

def main_loop():
    global awaiting_response
    thread_id = threading.get_ident()
    print(f"[THREAD] Main loop running in thread {thread_id}")
    
    # Start with an initial idle playlist
    idle_playlist_maker()
    
    # Initialize the background video player with a delay
    initialize_background_player()
    
    while not _shutdown_flag:
        awaiting_response = False
        idle_mode()

        # Wait here for response button to be pressed
        print("[MAIN] Idle finished, waiting for trigger")
        while not awaiting_response and not _shutdown_flag:
            time.sleep(1)  # Sleep without printing to reduce log spam
        
        # Check if we got shutdown while waiting
        if _shutdown_flag:
            break
            
        print("[MAIN] Response triggered, starting response processing")
        response_mode()
        
        # Add a delay to ensure the video has time to play
        time.sleep(10)
        
        # After response, create a new playlist for continued interaction
        print("[MAIN] Updating playlist with additional videos")
        create_lipsync_playlist()
        
        print("[MAIN] Response mode completed, ready for next interaction")
    
    print(f"[THREAD] Thread {thread_id} shutting down")

def trigger_response_with_prompt(prompt):
    global awaiting_response, user_prompt
    user_prompt = prompt
    awaiting_response = True
    print(f"[UI] Response triggered by user with prompt: {prompt[:50]}...")

def start_main_thread():
    global _main_thread
    with _thread_lock:
        if _main_thread is None or not _main_thread.is_alive():
            _main_thread = threading.Thread(target=main_loop, daemon=True)
            _main_thread.start()
            print(f"[INIT] Main thread started with ID {_main_thread.ident}")
            return True
        else:
            print(f"[INIT] Main thread already running with ID {_main_thread.ident}")
            return False

def shutdown():
    global _shutdown_flag
    _shutdown_flag = True
    print("[APP] Shutdown initiated, waiting for threads to terminate...")
    if _main_thread and _main_thread.is_alive():
        _main_thread.join(timeout=5)
    print("[APP] Shutdown complete")

# Register shutdown handler
atexit.register(shutdown)

# Add an endpoint to get the latest LLM response
@app.get('/get_response')
def get_response():
    global llm_response
    return {"response": llm_response}

# Only run this block when the file is executed directly
if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    # Build the UI with our response callback
    build_ui(trigger_response_callback=trigger_response_with_prompt)
    
    # Start the main thread
    start_main_thread()
    
    # Start the NiceGUI server
    ui.run()