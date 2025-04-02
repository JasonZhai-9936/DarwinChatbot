# controller.py

import time
import os
import threading
from LivePortraitIdle import start_generation_loop  # or from LivePortraitMain if renamed

# Shared flag
is_on = False

def get_is_on():
    return is_on

def toggle_loop():
    global is_on
    while True:
        is_on = True
        print("[CONTROL] isOn = True")
        time.sleep(8)
        is_on = False
        print("[CONTROL] isOn = False")
        time.sleep(5)

if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"[DEBUG] BASE_DIR is: {BASE_DIR}")

    # Start toggle thread
    threading.Thread(target=toggle_loop, daemon=True).start()

    # Start the generation loop with a custom number of chunks
    start_generation_loop(get_is_on, infinite_generation=False, num_chunks=3)
