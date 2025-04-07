# app.py

import threading
import time
import os
import glob
import atexit
from nicegui import ui, app

from LivePortraitIdle import generate_fixed_chunks
from LatentSync import run_latentsync_inference
from ui import build_ui
from PlaylistManager import idle_playlist_maker, response_playlist_maker

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")

# === Thread management ===
_main_thread = None
_thread_lock = threading.Lock()
_shutdown_flag = False

# === State Flags ===
awaiting_response = False  # flipped by UI button

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
    generate_fixed_chunks(mode="talking", chunks_per_video=1, video_limit=1)

    print("[MAIN] Idle mode finished, waiting for response trigger...")
    return

def response_mode():
    success = False
    print("[MAIN] Starting response mode...")

    response_playlist_maker()
    print("[PLACEHOLDER] Generating speech from LLM+TTS...")
    print(f"success is: {success}")

    success = run_latentsync_inference()
    print(f"success is: {success}")
    print("finished running latentsync")
    return

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
        
        # After response mode, watch for new video
        print("[MAIN] Response mode completed, watching for new video")
        new_video = await_latentsync_output()
        
        if new_video:
            print(f"[MAIN] Processing complete with video: {new_video}")
        else:
            print("[MAIN] Processing complete but no new video detected")
    
    print(f"[THREAD] Thread {thread_id} shutting down")

def trigger_response():
    global awaiting_response
    awaiting_response = True
    print("[UI] Response triggered by user")

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

# Build the UI with our trigger function
build_ui(trigger_response)

# Only run this block when the file is executed directly
if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    # Start the main thread only if it's not already running
    start_main_thread()
    
    # Start the NiceGUI server
    ui.run()