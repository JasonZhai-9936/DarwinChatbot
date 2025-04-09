# Run this to install LatentSync

# /.install_flags tracks if each separate install component has already been run
# If you're running into install issues, delete the /.install_flags folder

import os
import subprocess
import sys
import shutil
import platform

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

def run(command, cwd=None, shell=False, env=None):
    print(f"> Running: {' '.join(command) if isinstance(command, list) else command}")
    result = subprocess.run(command, cwd=cwd, shell=shell, env=env)
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

def verify_env():
    print(f"Verifying Conda env '{CONDA_ENV}'...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "python", "-c", f"import sys; print('Python in {CONDA_ENV}:', sys.executable)"
    ])

def install_venv():
    step = "install_venv"
    if check_flag(step):
        print(f"Skipping {step} (already done)")
        return
    print("Installing virtualenv...")
    run([
        "conda", "run", "-n", CONDA_ENV,
        "pip", "install", "virtualenv"
    ])
    set_flag(step)

def run_setup_script():
    step = "run_setup_script"
    if check_flag(step):
        print(f"Skipping {step} (already done)")
        return
    
    print("Running setup_env.sh...")
    
    # Determine the shell command based on platform
    if platform.system() == "Windows":
        # For Windows, we need to use bash from Git or WSL if available
        try:
            # Try with Git Bash
            env_vars = os.environ.copy()
            env_vars["CONDA_PREFIX"] = subprocess.check_output(
                ["conda", "run", "-n", CONDA_ENV, "python", "-c", "import os; print(os.environ.get('CONDA_PREFIX'))"],
                text=True
            ).strip()
            
            run(["bash", "setup_env.sh"], cwd=REPO_NAME, env=env_vars)
        except:
            print("Could not run setup_env.sh with bash. Please run it manually after activating the conda environment.")
            print("Commands to run:")
            print(f"  conda activate {CONDA_ENV}")
            print(f"  cd {REPO_NAME}")
            print("  bash setup_env.sh")
    else:
        # For Linux/macOS
        conda_prefix = subprocess.check_output(
            ["conda", "run", "-n", CONDA_ENV, "python", "-c", "import os; print(os.environ.get('CONDA_PREFIX'))"],
            text=True
        ).strip()
        
        setup_content = f"""#!/bin/bash
source "{conda_prefix}/etc/profile.d/conda.sh"
conda activate {CONDA_ENV}
cd {os.path.abspath(REPO_NAME)}
source setup_env.sh
"""
        
        setup_script = "run_setup_latentsync.sh"
        with open(setup_script, "w") as f:
            f.write(setup_content)
        
        os.chmod(setup_script, 0o755)
        run(["bash", setup_script])
        os.remove(setup_script)
    
    set_flag(step)

def run_full_setup():
    print("Starting LatentSync setup...")
    clone_repo()
    create_conda_env()
    verify_env()
    install_venv()
    
    # Run setup script or provide instructions
    try:
        run_setup_script()
        print("\nSetup complete!")
    except:
        print("\nPartial setup complete.")
        print("To complete the setup, run the following commands manually:")
        print(f"  conda activate {CONDA_ENV}")
        print(f"  cd {REPO_NAME}")
        print("  source setup_env.sh")
    
    print("\nTo use LatentSync:")
    print(f"  1. Activate the environment: conda activate {CONDA_ENV}")
    print(f"  2. Navigate to the repo: cd {REPO_NAME}")

if __name__ == "__main__":
    run_full_setup()