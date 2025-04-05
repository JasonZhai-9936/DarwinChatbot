# app.py

import threading
import time, os
from nicegui import ui, app
from controller import DarwinController
from LivePortraitIdle import generate_fixed_chunks
from LatentSync import run_latentsync_inference
from ui import build_ui
from PlaylistManager import idle_playlist_maker, response_playlist_maker

app.add_static_files('/stream', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stream')))


def control_loop():
    while True:
        if controller.is_response():
            response_playlist_maker()
            print("[INFO] Stage: Response_On - processing prompt & lipsync")
            print("[PLACEHOLDER] Generating speech from LLM+TTS...")

            success = run_latentsync_inference()
            if success:
                print("[INFO] Final video generated.")
            else:
                print("[ERROR] Failed to generate response video.")

            controller.set_idle()

        elif controller.is_idle():
            idle_playlist_maker()
            print("[INFO] Stage: Idle_On - generating idle chunks")
            generate_fixed_chunks(controller.is_idle, mode="idle", chunks_per_video=3)

        else:
            print("[WAITING] No active stage, sleeping...")
            time.sleep(1)

def delayed_control_loop_start():
    print("[INIT] Waiting 10 seconds for NiceGUI to start...")
    time.sleep(10)
    control_loop()

controller = DarwinController()
build_ui(controller)

# Start the control loop in a background thread
threading.Thread(target=delayed_control_loop_start, daemon=True).start()


# Start the UI

ui.run()
