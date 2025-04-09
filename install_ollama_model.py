#!/usr/bin/env python3
"""
Ollama and dolphin-mixtral Model Installer Script for container environments
This version uses direct binary download instead of the official installer
"""

import os
import sys
import platform
import subprocess
import time
import shutil
import tempfile
import requests
import tarfile
from pathlib import Path

# Constants
MODEL_NAME = "dolphin-mixtral"
OLLAMA_LINUX_URL = "https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64"
INSTALL_DIR = os.path.expanduser("~/bin")

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

def install_ollama_direct():
    """Install Ollama directly without requiring root privileges"""
    print("Installing Ollama directly from binary...")
    
    # Create install directory if it doesn't exist
    os.makedirs(INSTALL_DIR, exist_ok=True)
    
    # Download the Ollama binary
    print(f"Downloading Ollama from {OLLAMA_LINUX_URL}...")
    try:
        response = requests.get(OLLAMA_LINUX_URL, stream=True)
        response.raise_for_status()
        
        # Save the binary
        ollama_path = os.path.join(INSTALL_DIR, "ollama")
        with open(ollama_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Make it executable
        os.chmod(ollama_path, 0o755)
        
        # Add to PATH temporarily for this session
        os.environ['PATH'] = f"{INSTALL_DIR}:{os.environ['PATH']}"
        
        # Test if it works
        if is_ollama_installed():
            print(f"Ollama installed successfully at {ollama_path}")
            print(f"Version: {get_ollama_version()}")
            return True
        else:
            print("Ollama installation failed. Binary not found in PATH.")
            return False
    except Exception as e:
        print(f"Error installing Ollama: {e}")
        return False

def start_ollama_service():
    """Start the Ollama service in the background"""
    print("Starting Ollama service...")
    
    try:
        # Start in background and redirect output
        subprocess.Popen(
            ["ollama", "serve"], 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print("Started Ollama service in the background")
        
        # Wait for service to be ready
        print("Waiting for Ollama service to be ready...")
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Error starting Ollama service: {e}")
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
    
    # Only works on Linux
    if system != "Linux":
        print("This script is designed for Linux container environments only.")
        sys.exit(1)
    
    # Check if Ollama is already installed
    if is_ollama_installed():
        print(f"Ollama is already installed. Version: {get_ollama_version()}")
    else:
        # Install Ollama directly from binary
        success = install_ollama_direct()
        
        if not success:
            print("Ollama installation failed. Exiting.")
            sys.exit(1)
    
    # Start the Ollama service
    start_ollama_service()
    
    # Pull the model
    if pull_model(MODEL_NAME):
        # Verify the model installation
        if verify_model(MODEL_NAME):
            print(f"\nInstallation complete! You can now use Ollama with the {MODEL_NAME} model.")
            print(f"Example usage: ollama run {MODEL_NAME}")
            print(f"\nIMPORTANT: To use Ollama in future terminal sessions, add this to your ~/.bashrc:")
            print(f"export PATH=\"{INSTALL_DIR}:$PATH\"")
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