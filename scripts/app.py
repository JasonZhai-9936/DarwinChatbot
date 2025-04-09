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
from LLM import generate_darwin_response
from PlaylistManager import idle_playlist_maker, response_playlist_maker, create_lipsync_playlist

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  
STREAM_LIVE_DIR = os.path.join(REPO_DIR, "stream", "live")
STREAM_SPEECH_DIR = os.path.join(REPO_DIR, "stream", "speech")

# === Thread management ===
_main_thread = None
_thread_lock = threading.Lock()
_shutdown_flag = False

# === State Flags ===
awaiting_response = False
user_prompt = ""  # Store the user's prompt

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
    #generate_fixed_chunks(mode="talking", chunks_per_video=1, video_limit=1)

    print("[MAIN] Idle mode finished, waiting for response trigger...")
    return

def response_mode():
    global user_prompt
    print("[MAIN] Starting response mode...")

    # Update playlist for response mode
    response_playlist_maker()
    
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
    
    # Step 4: Update playlist with the latest generated video if successful
    if success:
        print("[PLAYLIST] Updating playlist with latest generated video")
        create_lipsync_playlist()
    
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
        
        # After response mode, watch for new video
        print("[MAIN] Response mode completed, watching for new video")
        new_video = await_latentsync_output()
        
        if new_video:
            print(f"[MAIN] Processing complete with video: {new_video}")
        else:
            print("[MAIN] Processing complete but no new video detected")
    
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

# Custom UI builder that integrates with our system
def build_ui():
    with ui.row().classes('w-full h-screen items-start justify-start gap-8 p-8'):
        # === VIDEO PLAYER ===
        with ui.column().classes('items-start'):
            video = ui.video(src='').props('autoplay muted controls') \
                .style('max-height: 100vh; aspect-ratio: 2 / 3; width: auto; height: auto; object-fit: cover;') \
                .classes('rounded-xl shadow-xl')

        playlist = []
        current_index = 0

        def load_playlist():
            nonlocal playlist, current_index
            PLAYLIST_PATH = os.path.join("stream", "playlist", "playlist.json")
            try:
                with open(PLAYLIST_PATH, "r") as f:
                    playlist = json.load(f)
                    current_index = 0
                    print(f"[UI] Loaded playlist with {len(playlist)} items")
            except Exception as e:
                print(f"[UI] Failed to load playlist: {e}")
                playlist = []

        def play_current_video():
            if current_index < len(playlist):
                PLAYLIST_FOLDER = "/stream"
                src = os.path.join(PLAYLIST_FOLDER, playlist[current_index])
                src = src.replace("\\", "/")
                video.props(f'src={src}?t={time.time()}')
                print(f"[UI] Playing: {src}")
            else:
                print("[UI] No videos to play")

        def play_next_video():
            nonlocal current_index
            current_index += 1
            if current_index < len(playlist):
                play_current_video()
            else:
                print("[UI] Reached end of playlist, reloading")
                load_playlist()
                play_current_video()

        video.on("ended", lambda _: play_next_video())
        load_playlist()
        play_current_video()

        # === RIGHT SIDE PANEL ===
        with ui.column().classes('items-start gap-4'):
            with ui.row().classes('items-center gap-4'):
                prompt_input = ui.input(label='Your prompt', placeholder='Type something...') \
                              .props('outlined') \
                              .classes('w-96')
                
                # Handle the user's prompt submission
                def submit_prompt():
                    user_text = prompt_input.value
                    if user_text and user_text.strip():
                        trigger_response_with_prompt(user_text)
                        prompt_input.value = ""  # Clear input after submission
                    else:
                        ui.notify("Please enter a prompt first", color="warning")
                
                ui.button('Ask Darwin', on_click=submit_prompt)

# Build our custom UI
build_ui()

# Only run this block when the file is executed directly
if __name__ in {"__main__", "__mp_main__"}:  # Support multiprocessing
    # Start the main thread only if it's not already running
    start_main_thread()
    
    # Make sure json is imported for playlist management
    import json
    
    # Start the NiceGUI server
    ui.run(host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))