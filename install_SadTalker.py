<<<<<<< HEAD
# Installs SadTalker model
=======
#Installs SadTalker model
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3

import os
import subprocess
import sys
import shutil

# === CONFIGURATION ===
REPO_NAME = "SadTalker"
REPO_URL = "https://github.com/OpenTalker/SadTalker.git"
CONDA_ENV = "SadTalker"  # Capitalized
PYTHON_VERSION = "3.8"
FLAGS_DIR = ".install_flags"

TORCH_PACKAGES = [
    "torch==1.12.1+cu113",
    "torchvision==0.13.1+cu113",
    "torchaudio==0.12.1"
]
TORCH_INDEX_URL = "https://download.pytorch.org/whl/cu113"

INSTALL_FFMPEG_CONDA = True
INSTALL_REQUIREMENTS_TXT = True
REQUIREMENTS_PATH = "requirements.txt"

# =======================

os.makedirs(FLAGS_DIR, exist_ok=True)

def flag_path(step):
    return os.path.join(FLAGS_DIR, f"{REPO_NAME}_{step}.flag")

def check_flag(step):
    return os.path.exists(flag_path(step))

def set_flag(step):
    open(flag_path(step), "w").close()

def run(command, cwd=None, shell=False):
    print(f"> Running: {' '.join(command) if isinstance(command, list) else command}")
    result = subprocess.run(command, cwd=cwd, shell=shell)
    if result.returncode != 0:
<<<<<<< HEAD
        print(f"Command failed: {command}")
=======
        print(f"❌ Command failed: {command}")
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
        sys.exit(1)

def clone_repo():
    if os.path.isdir(REPO_NAME):
        if not os.path.exists(os.path.join(REPO_NAME, ".git")):
<<<<<<< HEAD
            print(f"Incomplete repo found, deleting {REPO_NAME} and retrying...")
            shutil.rmtree(REPO_NAME)
        else:
            print(f"Repo already cloned: {REPO_NAME}")
            return
    print(f"Cloning {REPO_NAME}...")
    run(["git", "clone", REPO_URL])

def create_conda_env():
    print(f"Checking if Conda environment '{CONDA_ENV}' already exists...")
    result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
    if CONDA_ENV in result.stdout:
        print(f"Conda env '{CONDA_ENV}' already exists. Skipping creation.")
        return
    print(f"Creating Conda environment '{CONDA_ENV}' with Python {PYTHON_VERSION}...")
    run(["conda", "create", "-y", "-n", CONDA_ENV, f"python={PYTHON_VERSION}"])

def verify_env():
    print(f"Verifying Conda env '{CONDA_ENV}'...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "python", "-c", f"import sys; print('Python in {CONDA_ENV}:', sys.executable)"
=======
            print(f"⚠️ Incomplete repo found, deleting {REPO_NAME} and retrying...")
            shutil.rmtree(REPO_NAME)
        else:
            print(f"✅ Repo already cloned: {REPO_NAME}")
            return
    print(f"📦 Cloning {REPO_NAME}...")
    run(["git", "clone", REPO_URL])

def create_conda_env():
    print(f"🐍 Checking if Conda environment '{CONDA_ENV}' already exists...")
    result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
    if CONDA_ENV in result.stdout:
        print(f"✅ Conda env '{CONDA_ENV}' already exists. Skipping creation.")
        return
    print(f"🐍 Creating Conda environment '{CONDA_ENV}' with Python {PYTHON_VERSION}...")
    run(["conda", "create", "-y", "-n", CONDA_ENV, f"python={PYTHON_VERSION}"])

def verify_env():
    print(f"🔍 Verifying Conda env '{CONDA_ENV}'...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "python", "-c", f"import sys; print('✅ Python in {CONDA_ENV}:', sys.executable)"
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
    ])

def install_torch():
    step = "install_torch"
    if check_flag(step):
<<<<<<< HEAD
        print(f"Skipping {step} (already done)")
        return
    print(f"Installing PyTorch into '{CONDA_ENV}'...")
=======
        print(f"⏩ Skipping {step} (already done)")
        return
    print(f"📦 Installing PyTorch into '{CONDA_ENV}'...")
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
    run([
        "conda", "run", "-n", CONDA_ENV, "pip", "install", "-v", *TORCH_PACKAGES,
        "--extra-index-url", TORCH_INDEX_URL
    ], cwd=REPO_NAME)
    set_flag(step)

def install_ffmpeg():
    step = "install_ffmpeg"
    if check_flag(step):
<<<<<<< HEAD
        print(f"Skipping {step} (already done)")
        return
    if INSTALL_FFMPEG_CONDA:
        print("Installing ffmpeg via conda...")
=======
        print(f"⏩ Skipping {step} (already done)")
        return
    if INSTALL_FFMPEG_CONDA:
        print("🎞️ Installing ffmpeg via conda...")
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
        run(["conda", "install", "-y", "-n", CONDA_ENV, "ffmpeg"])
    set_flag(step)

def install_requirements():
    step = "install_requirements"
    if check_flag(step):
<<<<<<< HEAD
        print(f"Skipping {step} (already done)")
        return
    if INSTALL_REQUIREMENTS_TXT:
        print(f"Installing from {REQUIREMENTS_PATH}...")
=======
        print(f"⏩ Skipping {step} (already done)")
        return
    if INSTALL_REQUIREMENTS_TXT:
        print(f"📄 Installing from {REQUIREMENTS_PATH}...")
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
        run([
            "conda", "run", "-n", CONDA_ENV,
            "pip", "install", "-r", REQUIREMENTS_PATH
        ], cwd=REPO_NAME)
    set_flag(step)

def run_full_setup():
    clone_repo()
    create_conda_env()
    verify_env()
    install_torch()
    install_ffmpeg()
    install_requirements()
<<<<<<< HEAD
    print("Setup complete!")
=======
    print("✅ Setup complete!")
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3

if __name__ == "__main__":
    run_full_setup()
