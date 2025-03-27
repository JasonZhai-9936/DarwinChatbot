<<<<<<< HEAD
# Run this to install LivePortrait (you might need to pip install opencv-python if it asks)
=======
# Run this to install ALL requirements (you might need to pip install opencv-python if it asks)
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3

# /.install_flags tracks if each separate install component has already been run. 
# IF you're running into install issues, delete the /.install_flags folder

import os
import subprocess
import sys
import shutil

REPO_NAME = "LivePortrait"
REPO_URL = "https://github.com/KwaiVGI/LivePortrait"
CONDA_ENV = "LivePortrait"
PRETRAINED_DIR = "pretrained_weights"
FLAGS_DIR = ".install_flags"

# Ensure the flags directory exists
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
        print(f"❌ Command failed: {command}")
        sys.exit(1)

def clone_repo():
    if os.path.isdir(REPO_NAME):
        if not os.path.exists(os.path.join(REPO_NAME, ".git")):
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

    print(f"🐍 Creating Conda environment '{CONDA_ENV}' with Python 3.10...")
    run(["conda", "create", "-y", "-n", CONDA_ENV, "python=3.10"])

def verify_env():
    print(f"🔍 Verifying Conda env '{CONDA_ENV}'...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "python", "-c", f"import sys; print('✅ Python in {CONDA_ENV}:', sys.executable)"
    ])

def install_torch():
    step = "install_torch"
    if check_flag(step):
        print(f"⏩ Skipping {step} (already done)")
        return
    print(f"📦 Installing PyTorch into '{CONDA_ENV}' (CUDA 12.4)...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "pip", "install", "-v", "torch", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu124"
    ], cwd=REPO_NAME)
    set_flag(step)

def install_requirements():
    step = "install_requirements"
    if check_flag(step):
        print(f"⏩ Skipping {step} (already done)")
        return
    print(f"📄 Installing requirements.txt...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "pip", "install", "-r", "requirements.txt"
    ], cwd=REPO_NAME)
    set_flag(step)

def download_pretrained():
    step = "download_pretrained"
    if check_flag(step):
        print(f"⏩ Skipping {step} (already done)")
        return
    print("🎯 Downloading pretrained weights...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "huggingface-cli", "download", "KwaiVGI/LivePortrait",
        "--local-dir", PRETRAINED_DIR,
        "--exclude", "*.git*", "README.md", "docs"
    ], cwd=REPO_NAME)
    set_flag(step)

def install_other_requirements():
    step = "install_other_requirements"
    if check_flag(step):
        print(f"⏩ Skipping {step} (already done)")
        return

    print("🔧 Installing other required packages (OpenCV + FFmpeg + Tyro + ONNX + ONNXRuntime)...")

    run([
        "conda", "run", "-n", CONDA_ENV,
        "pip", "install", "opencv-python", "tyro", "onnx", "onnxruntime", "onnxruntime-gpu","sympy", "pykalman", "typing_extensions", "colorama", "torch", "pillow"
    ])

    run([
        "conda", "install", "-y", "-n", CONDA_ENV, "ffmpeg"
    ])

    set_flag(step)

def run_full_setup():
    clone_repo()
    create_conda_env()
    verify_env()
    install_torch()
    install_requirements()
    download_pretrained()
    install_other_requirements()
    print("✅ Setup complete!")

if __name__ == "__main__":
    run_full_setup()
