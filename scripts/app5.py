# app4.py - Updated with Groq TTS Integration

import threading
import time
import os, json
import glob
import atexit
from nicegui import ui, app
import random
from PlaylistManagerTest4 import load_scripted_playlist

# Import LLM function
from LLM_Groq4 import generate_darwin_response

# Import background functions
from BackgroundManager4 import initialize_background_player

# Import playlist functions
from PlaylistManagerTest4 import (
    idle_playlist_maker, 
    response_playlist_maker, 
    create_lipsync_playlist, 
    make_response_playlist_with_lipsync
)

from uiTest2 import build_ui 

# UPDATED: Import the new Groq TTS module instead of SparkTTS
from GroqTTS import run_tts_for_darwin


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
latest_speech_file = ""  # Store the latest speech file path

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
    global user_prompt, llm_response, latest_speech_file
    print("[MAIN] Starting response mode...")

    try:
        # Play lipsync video immediately
        print("[VIDEO] Creating and playing lipsync playlist...")
        make_response_playlist_with_lipsync()
        time.sleep(1)  # allow frontend to start playing

        # Now begin processing
        print(f"[LLM] Processing user prompt: {user_prompt[:50]}...")
        llm_response = generate_darwin_response(user_prompt)

        print(f"[LLM] Response generated: {llm_response[:300]}...")
        print("[LLM] FULL RESPONSE:")
        print("=============================")
        print(llm_response)
        print("=============================")

        # UPDATED: Use Groq TTS for speech generation
        print("[TTS] Converting text to speech using Groq PlayAI...")
        speech_file = run_tts_for_darwin(text=llm_response)
        
        if speech_file:
            latest_speech_file = speech_file
            print(f"[TTS] Speech generated successfully: {speech_file}")
            
            # Trigger audio playback on the frontend
            print("[AUDIO] Triggering audio playback on frontend...")
            # The frontend will check for new audio files via the API endpoint
            
        else:
            print("[TTS] Speech generation failed")
            latest_speech_file = ""

    except Exception as e:
        print(f"[ERROR] Failed to generate LLM response or speech: {e}")
        llm_response = "I beg your pardon, but I seem to be experiencing some difficulty in processing your query at the moment."
        latest_speech_file = ""

    user_prompt = ""
    return True

def main_loop():
    global awaiting_response
    thread_id = threading.get_ident()
    print(f"[THREAD] Main loop running in thread {thread_id}")
    
    # Load scripted playlist if present
    if not load_scripted_playlist():
        idle_playlist_maker()
        initialize_background_player()
    
    just_responded = False

    while not _shutdown_flag:
        awaiting_response = False

        # Only re-run idle mode if we didn't just finish a response
        if not just_responded:
            idle_mode()

        just_responded = False  # Reset flag
        
        print("[MAIN] Idle finished, waiting for trigger")
        while not awaiting_response and not _shutdown_flag:
            time.sleep(1)  
        
        if _shutdown_flag:
            break
            
        print("[MAIN] Response triggered, starting response processing")
        response_mode()

        time.sleep(3)

        print("[MAIN] Response mode completed, ready for next interaction")

        just_responded = True  # Skip idle playlist regen on next loop

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

# UPDATED: Enhanced API endpoints for speech integration
@app.get('/get_response')
def get_response():
    global llm_response
    return {"response": llm_response}

@app.get('/get_latest_speech')
def get_latest_speech():
    """API endpoint to get the latest speech file for playback"""
    global latest_speech_file
    if latest_speech_file and os.path.exists(latest_speech_file):
        # Convert path to web-accessible path, avoiding duplication
        if latest_speech_file.startswith("stream"):
            # Path already starts with "stream", just add leading slash and convert separators
            web_path = f"/{latest_speech_file.replace(os.sep, '/')}"
        else:
            # Convert absolute path to relative path
            relative_path = os.path.relpath(latest_speech_file, REPO_DIR)
            # Remove "stream/" prefix if it exists to avoid duplication
            if relative_path.startswith("stream/") or relative_path.startswith("stream\\"):
                relative_path = relative_path[7:]
            web_path = f"/stream/{relative_path.replace(os.sep, '/')}"
        
        print(f"[DEBUG] Speech file path: {latest_speech_file}")
        print(f"[DEBUG] Web path: {web_path}")
        return {"speech_file": web_path, "available": True}
    else:
        return {"speech_file": "", "available": False}

@app.get('/clear_speech')
def clear_speech():
    """Clear the current speech file (called after playback)"""
    global latest_speech_file
    latest_speech_file = ""
    return {"status": "cleared"}

# Only run this block when the file is executed directly
if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    # Build the UI with our response callback
    build_ui(trigger_response_callback=trigger_response_with_prompt)
    
    # Start the main thread
    start_main_thread()
    
    # Start the NiceGUI server
    ui.run()