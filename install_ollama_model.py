#!/usr/bin/env python3
"""
Ollama and dolphin-mixtral Model Installer Script
Compatible with both Windows and Linux systems
"""

import os
import sys
import platform
import subprocess
import time
import shutil
import tempfile
import requests
from pathlib import Path

# Constants
MODEL_NAME = "dolphin-mixtral"
OLLAMA_WINDOWS_URL = "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip"
WINDOWS_INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Ollama')

def run_command(cmd, shell=False, check=True, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            check=check, 
            text=True,
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Command output: {e.stdout if hasattr(e, 'stdout') else ''}")
        print(f"Command error: {e.stderr if hasattr(e, 'stderr') else ''}")
        return e

def is_ollama_installed():
    """Check if Ollama is already installed"""
    ollama_path = shutil.which("ollama")
    return ollama_path is not None

def get_ollama_version():
    """Get the installed Ollama version"""
    try:
        result = run_command(["ollama", "--version"])
        if result.returncode == 0:
            return result.stdout.strip()
        return "Unknown"
    except Exception as e:
        return f"Error getting version: {e}"

def install_ollama_linux():
    """Install Ollama on Linux"""
    print("Installing Ollama on Linux...")
    
    # Use the official install script
    cmd = "curl -fsSL https://ollama.com/install.sh | sh"
    result = run_command(cmd, shell=True)
    
    if is_ollama_installed():
        print(f"Ollama installed successfully. Version: {get_ollama_version()}")
        return True
    else:
        print(f"Ollama installation failed. Please check the output.")
        return False

def start_ollama_service_linux():
    """Start the Ollama service on Linux"""
    print("Starting Ollama service...")
    
    # Try both systemd and manual service start
    try:
        # First try systemd
        run_command(["systemctl", "start", "ollama.service"], check=False)
    except Exception:
        # Fall back to manual start
        try:
            # Start in background and redirect output
            subprocess.Popen(
                ["ollama", "serve"], 
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            print("Started Ollama service manually")
        except Exception as e:
            print(f"Error starting Ollama service: {e}")
            return False
    
    # Wait for service to be ready
    print("Waiting for Ollama service to be ready...")
    time.sleep(5)
    return True

def install_ollama_windows():
    """Install Ollama on Windows"""
    print("Installing Ollama on Windows...")
    
    # Create temp directory for download
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "ollama.zip")
    
    try:
        # Download the latest Ollama release
        print(f"Downloading Ollama from {OLLAMA_WINDOWS_URL}...")
        response = requests.get(OLLAMA_WINDOWS_URL, stream=True)
        response.raise_for_status()
        
        # Save the zip file
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Create install directory if it doesn't exist
        os.makedirs(WINDOWS_INSTALL_DIR, exist_ok=True)
        
        # Extract the zip file
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(WINDOWS_INSTALL_DIR)
        
        # Add to PATH if not already there
        ollama_path = os.path.join(WINDOWS_INSTALL_DIR, 'ollama.exe')
        if os.path.exists(ollama_path):
            print(f"Ollama extracted to {WINDOWS_INSTALL_DIR}")
            
            # Add to PATH temporarily for this session
            os.environ['PATH'] = f"{WINDOWS_INSTALL_DIR};{os.environ['PATH']}"
            
            # Start the Ollama service
            start_ollama_service_windows()
            return True
        else:
            print(f"Ollama executable not found after extraction")
            return False
            
    except Exception as e:
        print(f"Error installing Ollama on Windows: {e}")
        return False
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def start_ollama_service_windows():
    """Start the Ollama service on Windows"""
    print("Starting Ollama service...")
    
    try:
        # Start Ollama service in background
        ollama_exe = os.path.join(WINDOWS_INSTALL_DIR, 'ollama.exe')
        
        # Kill any existing Ollama processes
        try:
            run_command(["taskkill", "/F", "/IM", "ollama.exe"], check=False)
            time.sleep(1)
        except:
            pass
            
        # Start the service
        subprocess.Popen(
            [ollama_exe, "serve"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for service to start
        print("Waiting for Ollama service to be ready...")
        time.sleep(10)
        return True
    except Exception as e:
        print(f"Error starting Ollama service on Windows: {e}")
        return False

def pull_model(model_name):
    """Pull the specified model"""
    print(f"Pulling {model_name} model (this may take some time)...")
    result = run_command(["ollama", "pull", model_name])
    
    if result.returncode == 0:
        return True
    else:
        print(f"Error pulling model: {result.stderr if hasattr(result, 'stderr') else ''}")
        return False

def verify_model(model_name):
    """Verify the model was installed correctly"""
    print(f"Verifying {model_name} model installation...")
    result = run_command(["ollama", "list"])
    
    if model_name in result.stdout:
        print(f"Success! The {model_name} model has been installed.")
        print("Model details:")
        for line in result.stdout.splitlines():
            if model_name in line:
                print(line)
        return True
    else:
        print(f"Error: Failed to verify model installation.")
        return False

def main():
    """Main installation function"""
    system = platform.system()
    print(f"Detected operating system: {system}")
    print(f"Python version: {platform.python_version()}")
    
    # Check if Ollama is already installed
    if is_ollama_installed():
        print(f"Ollama is already installed. Version: {get_ollama_version()}")
    else:
        # Install Ollama based on the operating system
        if system == "Windows":
            success = install_ollama_windows()
        else:  # Linux
            success = install_ollama_linux()
        
        if not success:
            print("Ollama installation failed. Exiting.")
            sys.exit(1)
    
    # Start the Ollama service
    if system == "Windows":
        start_ollama_service_windows()
    else:  # Linux
        start_ollama_service_linux()
    
    # Pull the model
    if pull_model(MODEL_NAME):
        # Verify the model installation
        if verify_model(MODEL_NAME):
            print(f"\nInstallation complete! You can now use Ollama with the {MODEL_NAME} model.")
            print(f"Example usage: ollama run {MODEL_NAME}")
        else:
            print("\nModel verification failed. Please check the logs above for errors.")
    else:
        print("\nFailed to pull the model. Please check your internet connection and try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)