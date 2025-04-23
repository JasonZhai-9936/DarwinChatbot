# app.py

import threading
import time
import os, json
import glob
import atexit
from nicegui import ui, app

from LivePortraitIdle import generate_fixed_chunks
from LatentSync import run_latentsync_inference
from SparkTTS import run_tts
from Dual_LLM import generate_darwin_response
from PlaylistManager import idle_playlist_maker, response_playlist_maker, create_lipsync_playlist
from ui import build_ui  # Import build_ui from the ui.py file

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
    idle_playlist_maker()
    #generate_fixed_chunks(mode="talking", chunks_per_video=1, video_limit=1)

    print("[MAIN] Idle mode finished, waiting for response trigger...")
    return

def response_mode():
    global user_prompt
    print("[MAIN] Starting response mode...")
    
    # Step 1: Generate response from the LLM
    print("[LLM] Generating Darwin's response...")
    if not user_prompt:
        print("[WARNING] No user prompt provided, using default")
        user_prompt = "Tell me about your theory of evolution."
        
    llm_response = generate_darwin_response(user_prompt)
    print(f"[LLM] Response generated: {llm_response[:100]}...")
    
    # Step 2: Convert response to speech using TTS
    print("[TTS] Converting text to speech...")
    speech_file = run_tts(text=llm_response)
    print(f"[TTS] Speech generated: {speech_file}")
    
    # Step 3: Generate lip-synced video
    print("[SYNC] Running lip sync...")
    success = run_latentsync_inference()
    print(f"[SYNC] Lip sync completed with status: {success}")
    
    # Step 4: If successful, get the latest video and make it the only item in the playlist
    if success:
        # Get the latest video from the LIVE_DIR
        latest_video = get_latest_video_from_live_dir()
        if latest_video:
            print(f"[PLAYBACK] Found latest video: {latest_video}")
            # Update playlist to only include this video, forcing playback
            update_playlist_with_single_video(latest_video)
            # The updated UI will automatically detect playlist changes and play the video
        else:
            print("[ERROR] No video found in live directory after sync completion")
    
    # Reset the user prompt for next interaction
    user_prompt = ""
    
    return success

def main_loop():
    global awaiting_response
    thread_id = threading.get_ident()
    print(f"[THREAD] Main loop running in thread {thread_id}")
    
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
        
        # Add a delay to ensure the video has time to play (the response video)
        time.sleep(10)
        
        # After showing the response video, update the playlist to include other videos too
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

# Only run this block when the file is executed directly
if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    # Build the UI with our response callback
    build_ui(trigger_response_callback=trigger_response_with_prompt)
    
    # Start the main thread
    start_main_thread()
    
    # Start the NiceGUI server
    ui.run()