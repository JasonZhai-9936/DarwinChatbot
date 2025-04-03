# controller.py

import os
import sys
import time
import threading

# Add scripts/ to path
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.append(SCRIPT_DIR)

from LivePortraitIdle import generate_fixed_chunks
from LatentSync import run_latentsync_inference


class Controller:
    def __init__(self):
        self.run_idle = True
        self.run_lipsync = False

        self.BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))
        print(f"[DEBUG] BASE_DIR is: {self.BASE_DIR}")

        threading.Thread(target=self.control_loop, daemon=False).start()

    # === Flag Getters/Setters ===
    def get_run_idle(self):
        return self.run_idle

    def set_run_idle(self, value: bool):
        print(f"[DEBUG] Setting run_idle = {value}")
        self.run_idle = value

    def get_run_lipsync(self):
        return self.run_lipsync

    def set_run_lipsync(self, value: bool):
        print(f"[DEBUG] Setting run_lipsync = {value}")
        self.run_lipsync = value

    # === Main control loop ===
    def control_loop(self): 
        while True:
            if self.run_lipsync:
                print("[INFO] Running LatentSync lipsync inference...")
                success = run_latentsync_inference()
                if success:
                    print("[INFO] Lipsync completed successfully.")
                else:
                    print("[WARN] Lipsync failed.")
                self.set_run_lipsync(False)
                self.set_run_idle(True)

            elif self.run_idle:
                print("[INFO] Running idle chunk generation...")
                generate_fixed_chunks(self.get_run_idle, mode="idle", chunks_per_video=3, video_limit=20)
            else:
                print("[WAIT] No flags set. Sleeping for a bit...")
                time.sleep(2)


# === Example trigger: replace this with real event or Flask route later ===
def demo_trigger_lipsync(controller: Controller):
    time.sleep(3)  # Wait 30 seconds before triggering
    print("[DEMO] Triggering lipsync task after 30s delay...")
    controller.set_run_idle(False)
    controller.set_run_lipsync(True)


if __name__ == "__main__":
    controller = Controller()
    threading.Thread(target=demo_trigger_lipsync, args=(controller,), daemon=True).start()
