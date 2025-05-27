# app_runpod.py

import threading
import time
import os, json
import glob
import atexit
import queue
from nicegui import ui, app

from LivePortraitIdle import generate_fixed_chunks
from LatentSync import run_latentsync_inference
from SparkTTS import run_tts
from LLM import generate_darwin_response
from scripts.old.PlaylistManager import idle_playlist_maker, response_playlist_maker, create_lipsync_playlist
from Unused.ui_runpod import build_ui  # Import our improved UI

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")
STREAM_SPEECH_DIR = os.path.join(REPO_DIR, "stream", "speech")

# === Thread management ===
_main_thread = None
_thread_lock = threading.Lock()
_shutdown_flag = False

# === State Flags and Message Queue ===
_state_lock = threading.Lock()
awaiting_response = False
user_prompt_queue = queue.Queue()  # Thread-safe queue for prompts

# Expose media folder
app.add_static_files('/stream', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stream')))

def await_latentsync_output(timeout=300, poll_interval=2):
    print(f"[WAIT] Watching {STREAM_LIVE_DIR} for new video...")

    # Step 1: Get initial list of .mp4 files
    existing_files = set(glob.glob(os.path.join(STREAM_LIVE_DIR, "*.mp4")))
    start_time = time.time()

    while time.time() - start_time < timeout and not _shutdown_flag:
        current_files = set(glob.glob(os.path.join(STREAM_LIVE_DIR, "*.mp4")))
        new_files = current_files - existing_files

        if new_files:
            new_file = list(new_files)[0]
            print(f"[FOUND] New video detected: {new_file}")
            return new_file

        time.sleep(poll_interval)

    print(f"[TIMEOUT] No new video found in {STREAM_LIVE_DIR} within {timeout} seconds.")
    return None

def idle_mode():
    print("[MAIN] Starting idle mode...")
    idle_playlist_maker()
    # Note: generate_fixed_chunks is commented out as we're assuming videos are pre-generated
    # generate_fixed_chunks(mode="talking", chunks_per_video=1, video_limit=1)

    print("[MAIN] Idle mode finished, waiting for response trigger...")
    return

def response_mode():
    global user_prompt_queue
    print("[MAIN] Starting response mode...")

    # Update playlist for response mode
    response_playlist_maker()
    
    # Get the prompt from the queue
    try:
        user_prompt = user_prompt_queue.get(block=False)
        print(f"[MAIN] Processing prompt: {user_prompt[:50]}...")
    except queue.Empty:
        print("[WARNING] No user prompt in queue, using default")
        user_prompt = "Tell me about your theory of evolution."
    
    # Step 1: Generate response from the LLM
    print("[LLM] Generating Darwin's response...")
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
    
    # Step 4: Update playlist with the latest generated video if successful
    if success:
        print("[PLAYLIST] Updating playlist with latest generated video")
        create_lipsync_playlist()
    
    return success

def main_loop():
    global awaiting_response
    thread_id = threading.get_ident()
    print(f"[THREAD] Main loop running in thread {thread_id}")
    
    while not _shutdown_flag:
        with _state_lock:
            awaiting_response = False
        
        idle_mode()

        # Wait here for response button to be pressed
        print("[MAIN] Idle finished, waiting for trigger")
        while True:
            with _state_lock:
                if awaiting_response or _shutdown_flag:
                    break
            time.sleep(1)  # Sleep without printing to reduce log spam
        
        # Check if we got shutdown while waiting
        if _shutdown_flag:
            break
            
        print("[MAIN] Response triggered, starting response processing")
        response_mode()
        
        # After response mode, watch for new video
        print("[MAIN] Response mode completed, watching for new video")
        new_video = await_latentsync_output()
        
        if new_video:
            print(f"[MAIN] Processing complete with video: {new_video}")
        else:
            print("[MAIN] Processing complete but no new video detected")
    
    print(f"[THREAD] Thread {thread_id} shutting down")

def trigger_response_with_prompt(prompt):
    global awaiting_response, user_prompt_queue
    
    # Add the prompt to the queue
    user_prompt_queue.put(prompt)
    
    # Set the flag to trigger response mode
    with _state_lock:
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


build_ui(trigger_response_with_prompt)

# Only run this block when the file is executed directly
if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    # Start the main thread only if it's not already running
    start_main_thread()
    
    # Make sure json is imported for playlist management
    import json
    
    # Start the NiceGUI server
    ui.run()