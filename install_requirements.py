#main installer that calls all separate model installers

import subprocess
import sys


INSTALL_LIST = [
    "install_LivePortrait.py",
<<<<<<< HEAD
    #"install_SadTalker.py",
    #not used yet
=======
    "install_SadTalker.py",
  
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
]

def run_installers():
    for script in INSTALL_LIST:
        print(f"\n🚀 Running installer: {script}")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"❌ {script} failed. Exiting.")
            sys.exit(1)
        print(f"✅ {script} completed successfully.\n")

if __name__ == "__main__":
    run_installers()
