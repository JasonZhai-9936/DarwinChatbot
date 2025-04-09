# Run this to install LatentSync

import os
import subprocess
import sys
import shutil

REPO_NAME = "LatentSync"
REPO_URL = "https://github.com/bytedance/LatentSync.git"
CONDA_ENV = "latentsync"
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

    print(f"Creating Conda environment '{CONDA_ENV}' with Python 3.10...")
    run(["conda", "create", "-y", "-n", CONDA_ENV, "python=3.10"])

def setup_environment():
    step = "setup_environment"
    if check_flag(step):
        print(f"Skipping {step} (already done)")
        return
    
    print("Setting up environment using setup_env.sh...")
    
    # Create a temporary script to source setup_env.sh within conda environment
    setup_script = f"""
#!/bin/bash
source activate {CONDA_ENV}
cd {REPO_NAME}
source setup_env.sh
"""
    
    # Write the temporary script
    with open("temp_setup.sh", "w") as f:
        f.write(setup_script)
    
    # Make it executable
    os.chmod("temp_setup.sh", 0o755)
    
    # Run the setup script
    if sys.platform == "win32":
        print("Windows detected. Please run the following commands manually after this script completes:")
        print(f"conda activate {CONDA_ENV}")
        print(f"cd {REPO_NAME}")
        print("bash setup_env.sh")
    else:
        run(["bash", "./temp_setup.sh"], shell=False)
    
    # Clean up
    if os.path.exists("temp_setup.sh"):
        os.remove("temp_setup.sh")
    
    set_flag(step)

def verify_installation():
    print(f"Verifying LatentSync installation in '{CONDA_ENV}'...")
    try:
        run([
            "conda", "run", "-n", CONDA_ENV,
            "python", "-c", 
            "import torch; print(f'PyTorch version: {torch.__version__}'); "
            "print(f'CUDA available: {torch.cuda.is_available()}')"
        ])
        print("PyTorch verification successful.")
    except:
        print("PyTorch verification failed. Installation might be incomplete.")

def run_full_setup():
    print("Starting LatentSync setup...")
    clone_repo()
    create_conda_env()
    setup_environment()
    verify_installation()
    
    print("\nSetup complete!")
    print("\nTo use LatentSync:")
    print(f"  1. Activate the environment: conda activate {CONDA_ENV}")
    print(f"  2. Navigate to the repo: cd {REPO_NAME}")
    print("  3. Run your scripts")

if __name__ == "__main__":
    run_full_setup()