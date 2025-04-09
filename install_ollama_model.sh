#!/bin/bash
set -e

echo "Starting Ollama installation script..."

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo."
  exit 1
fi

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
  echo "Ollama is already installed. Checking version..."
  ollama --version
else
  echo "Installing Ollama..."
  
  # Install Ollama using their official script
  curl -fsSL https://ollama.com/install.sh | sh
  
  # Check if installation was successful
  if ! command -v ollama &> /dev/null; then
    echo "Ollama installation failed. Please check logs above for errors."
    exit 1
  fi
  
  echo "Ollama installed successfully!"
fi

# Start the Ollama service
echo "Starting Ollama service..."
systemctl enable --now ollama.service 2>/dev/null || true
systemctl start ollama.service 2>/dev/null || true

# Wait for Ollama service to be fully up
echo "Waiting for Ollama service to be ready..."
sleep 5

# Pull the specific model
echo "Pulling dolphin-mixtral model (this may take some time depending on your internet speed)..."
ollama pull dolphin-mixtral

# Verify the model was downloaded correctly
echo "Verifying model installation..."
if ollama list | grep -q "dolphin-mixtral"; then
  echo "Success! The dolphin-mixtral model has been installed."
  echo "Model details:"
  ollama list | grep "dolphin-mixtral"
else
  echo "Error: Failed to verify model installation. Please check if there were any errors above."
  exit 1
fi

echo "Installation complete! You can now use Ollama with the dolphin-mixtral model."
echo "Example usage: ollama run dolphin-mixtral"