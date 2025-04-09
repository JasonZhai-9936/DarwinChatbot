# Run this to install Spark-TTS

import os
import subprocess
import sys
import shutil

REPO_NAME = "Spark-TTS"
REPO_URL = "https://github.com/SparkAudio/Spark-TTS.git"
CONDA_ENV = "sparktts"
PRETRAINED_DIR = "pretrained_models"
MODEL_REPO = "SparkAudio/Spark-TTS-0.5B"
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
        print(f"Command failed: {command}")
        sys.exit(1)
    return result

def clone_repo():
    if os.path.isdir(REPO_NAME):
        if not os.path.exists(os.path.join(REPO_NAME, ".git")):
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

    print(f"Creating Conda environment '{CONDA_ENV}' with Python 3.12...")
    run(["conda", "create", "-y", "-n", CONDA_ENV, "python=3.12"])

def verify_env():
    print(f"Verifying Conda env '{CONDA_ENV}'...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "python", "-c", f"import sys; print('Python in {CONDA_ENV}:', sys.executable)"
    ])

def install_requirements():
    step = "install_requirements"
    if check_flag(step):
        print(f"Skipping {step} (already done)")
        return
    print(f"Installing requirements.txt...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "pip", "install", "-r", "requirements.txt"
    ], cwd=REPO_NAME)
    set_flag(step)

def check_git_lfs():
    step = "check_git_lfs"
    if check_flag(step):
        print(f"Skipping {step} (already done)")
        return
    
    print("Checking if git-lfs is installed...")
    try:
        result = run(["git", "lfs", "version"], capture_output=True)
        print("git-lfs is installed")
    except:
        print("git-lfs not found. Attempting to install...")
        try:
            if sys.platform == "darwin":  # macOS
                run(["brew", "install", "git-lfs"])
            elif sys.platform == "linux":
                # Try apt-get for Debian/Ubuntu
                try:
                    run(["apt-get", "update"])
                    run(["apt-get", "install", "-y", "git-lfs"])
                except:
                    # Try yum for CentOS/RHEL
                    run(["yum", "install", "-y", "git-lfs"])
            elif sys.platform == "win32":
                print("Please install git-lfs manually from https://git-lfs.com")
                print("   After installation, run 'git lfs install' and rerun this script")
                sys.exit(1)
        except:
            print("Could not automatically install git-lfs")
            print("Please install git-lfs manually from https://git-lfs.com")
            print("   After installation, run 'git lfs install' and rerun this script")
            sys.exit(1)
    
    print("Setting up git-lfs...")
    run(["git", "lfs", "install"])
    set_flag(step)

def download_pretrained():
    step = "download_pretrained"
    if check_flag(step):
        print(f"Skipping {step} (already done)")
        return
    
    pretrained_path = os.path.join(REPO_NAME, PRETRAINED_DIR)
    os.makedirs(pretrained_path, exist_ok=True)
    
    model_path = os.path.join(pretrained_path, "Spark-TTS-0.5B")
    if os.path.exists(model_path):
        print(f"Model already downloaded to {model_path}")
        set_flag(step)
        return
        
    print(f"Downloading pretrained model from {MODEL_REPO}...")
    run([
        "git", "clone", f"https://huggingface.co/{MODEL_REPO}", model_path
    ])
    set_flag(step)

def run_full_setup():
    print("Starting Spark-TTS setup...")
    clone_repo()
    create_conda_env()
    verify_env()
    install_requirements()
    check_git_lfs()
    download_pretrained()
    
    print("\nSetup complete!")
    print("\nTo use Spark-TTS:")
    print(f"  1. Activate the environment: conda activate {CONDA_ENV}")
    print(f"  2. Navigate to the repo: cd {REPO_NAME}")
    print("  3. Run your inference scripts")

if __name__ == "__main__":
    run_full_setup()