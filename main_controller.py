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
        self.Idle_On = True
        self.Lipsync_On = False
        self.LLM_On = False

        self.BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))
        print(f"[DEBUG] BASE_DIR is: {self.BASE_DIR}")

        threading.Thread(target=self.control_loop, daemon=False).start()

    
    def get_Idle_On(self):
        return self.Idle_On

    def set_Idle_On(self, value: bool):
        print(f"[DEBUG] Setting Idle_On = {value}")
        self.Idle_On = value

    def get_Lipsync_On(self):
        return self.Lipsync_On

    def set_Lipsync_On(self, value: bool):
        print(f"[DEBUG] Setting Lipsync_On = {value}")
        self.Lipsync_On = value

    # === Main control loop ===
    def control_loop(self): 
        while True:
            if self.Lipsync_On:
                print("[INFO] Running LatentSync lipsync inference...")
                success = run_latentsync_inference()
                if success:
                    print("[INFO] Lipsync completed successfully.")
                else:
                    print("[WARN] Lipsync failed.")
                self.set_Lipsync_On(False)
                self.set_Idle_On(True)

            elif self.LLM_On:
                pass

            elif self.Idle_On:
                print("[INFO] Running idle chunk generation...")
                generate_fixed_chunks(self.get_Idle_On, mode="idle", chunks_per_video=3, video_limit=20)
            else:
                print("[WAIT] No flags set. Sleeping for a bit...")
                time.sleep(2)



def demo_trigger_lipsync(controller: Controller):
    time.sleep(3)  # Wait 10 seconds before triggering
    print("[DEMO] Triggering lipsync task after 30s delay...")
    controller.set_Idle_On(False)
    controller.set_Lipsync_On(True)


if __name__ == "__main__":
    controller = Controller()
    threading.Thread(target=demo_trigger_lipsync, args=(controller,), daemon=True).start()
