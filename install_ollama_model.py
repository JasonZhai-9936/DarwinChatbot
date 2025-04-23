#!/usr/bin/env python3
"""
Ollama and dolphin-mixtral Model Installer Script for container environments
This version correctly handles the tarball structure and directly copies the binary
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
OLLAMA_LINUX_URL = "https://ollama.com/download/ollama-linux-amd64.tgz"
INSTALL_DIR = "/data/DarwinChatbot"

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

def install_ollama_manual():
    """Install Ollama using the official tarball without requiring root privileges"""
    print("Installing Ollama using official tarball...")
    
    # Create temp directory for download and extraction
    temp_dir = tempfile.mkdtemp()
    tarball_path = os.path.join(temp_dir, "ollama-linux-amd64.tgz")
    extract_dir = os.path.join(temp_dir, "extract")
    os.makedirs(extract_dir, exist_ok=True)
    
    try:
        # Download the Ollama tarball
        print(f"Downloading Ollama from {OLLAMA_LINUX_URL}...")
        response = requests.get(OLLAMA_LINUX_URL, stream=True)
        response.raise_for_status()
        
        # Save the tarball
        with open(tarball_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Create install directory if it doesn't exist
        os.makedirs(INSTALL_DIR, exist_ok=True)
        
        # Extract the tarball to the temp directory first
        print(f"Extracting Ollama to temporary directory...")
        with tarfile.open(tarball_path, 'r:gz') as tar:
            # List the contents to debug
            content_list = tar.getnames()
            print(f"Tarball contents: {content_list}")
            
            # Extract to temp directory
            tar.extractall(path=extract_dir)
        
        # Find the ollama binary in the extracted files
        ollama_binary = None
        for root, dirs, files in os.walk(extract_dir):
            if "ollama" in files:
                ollama_binary = os.path.join(root, "ollama")
                break
        
        # If we found the binary, copy it to the install directory
        if ollama_binary:
            print(f"Found ollama binary at {ollama_binary}")
            shutil.copy2(ollama_binary, os.path.join(INSTALL_DIR, "ollama"))
            os.chmod(os.path.join(INSTALL_DIR, "ollama"), 0o755)  # Make executable
        else:
            # Try other common patterns
            if "ollama" in content_list:
                print("Found ollama at root level")
                shutil.copy2(os.path.join(extract_dir, "ollama"), os.path.join(INSTALL_DIR, "ollama"))
                os.chmod(os.path.join(INSTALL_DIR, "ollama"), 0o755)
            elif "usr/bin/ollama" in content_list:
                print("Found ollama in usr/bin")
                shutil.copy2(os.path.join(extract_dir, "usr/bin/ollama"), os.path.join(INSTALL_DIR, "ollama"))
                os.chmod(os.path.join(INSTALL_DIR, "ollama"), 0o755)
            else:
                print(f"Could not find ollama binary in extracted files")
                return False
        
        # Add to PATH temporarily for this session
        os.environ['PATH'] = f"{INSTALL_DIR}:{os.environ['PATH']}"
        
        # Test if it works
        if is_ollama_installed():
            print(f"Ollama installed successfully at {INSTALL_DIR}/ollama")
            print(f"Version: {get_ollama_version()}")
            return True
        else:
            print("Ollama installation failed. Binary not found in PATH.")
            # Let's try to run it directly to see the error
            binary_path = os.path.join(INSTALL_DIR, "ollama")
            if os.path.exists(binary_path):
                print(f"Binary exists at {binary_path}, attempting to run directly...")
                try:
                    result = subprocess.run([binary_path, "--version"], text=True, capture_output=True)
                    print(f"Direct execution result: {result.stdout}")
                    print(f"Direct execution error: {result.stderr}")
                except Exception as e:
                    print(f"Error running binary directly: {e}")
            return False
    except Exception as e:
        print(f"Error installing Ollama: {e}")
        return False
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def start_ollama_service():
    """Start the Ollama service in the background"""
    print("Starting Ollama service...")
    
    try:
        # Try running ollama directly from the install path first
        ollama_path = os.path.join(INSTALL_DIR, "ollama")
        
        # Start in background and redirect output
        subprocess.Popen(
            [ollama_path, "serve"], 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print("Started Ollama service in the background")
        
        # Wait for service to be ready
        print("Waiting for Ollama service to be ready...")
        time.sleep(10)  # Wait longer for service initialization
        return True
    except Exception as e:
        print(f"Error starting Ollama service: {e}")
        return False

def pull_model(model_name):
    """Pull the specified model"""
    print(f"Pulling {model_name} model (this may take some time)...")
    # Use the direct path for more reliability
    ollama_path = os.path.join(INSTALL_DIR, "ollama")
    result = run_command([ollama_path, "pull", model_name])
    
    if result.returncode == 0:
        return True
    else:
        print(f"Error pulling model: {result.stderr if hasattr(result, 'stderr') else ''}")
        return False

def verify_model(model_name):
    """Verify the model was installed correctly"""
    print(f"Verifying {model_name} model installation...")
    # Use the direct path for more reliability
    ollama_path = os.path.join(INSTALL_DIR, "ollama")
    result = run_command([ollama_path, "list"])
    
    if result.returncode == 0 and model_name in result.stdout:
        print(f"Success! The {model_name} model has been installed.")
        print("Model details:")
        for line in result.stdout.splitlines():
            if model_name in line:
                print(line)
        return True
    else:
        print(f"Error: Failed to verify model installation.")
        if hasattr(result, 'stderr'):
            print(f"Error output: {result.stderr}")
        return False

def main():
    """Main installation function"""
    system = platform.system()
    print(f"Detected operating system: {system}")
    print(f"Python version: {platform.python_version()}")
    
    # Only works on Linux
    if system != "Linux":
        print("This script is designed for Linux environments only.")
        sys.exit(1)
    
    # Check if Ollama is already installed
    if is_ollama_installed():
        print(f"Ollama is already installed. Version: {get_ollama_version()}")
    else:
        # Install Ollama using the manual method
        success = install_ollama_manual()
        
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
            print(f"Example usage: {INSTALL_DIR}/ollama run {MODEL_NAME}")
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