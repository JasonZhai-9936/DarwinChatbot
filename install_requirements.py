#main installer that calls all separate model installers

import subprocess
import sys


INSTALL_LIST = [
    "install_LivePortrait.py",
    "install_ollama_model.py",
    "install_sparktts.py",
    "install_latentsync.py"
]

def run_installers():
    for script in INSTALL_LIST:
        print(f"\nRunning installer: {script}")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"{script} failed. Exiting.")
            sys.exit(1)
        print(f"{script} completed successfully.\n")

if __name__ == "__main__":
    run_installers()
