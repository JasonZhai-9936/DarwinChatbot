# DarwinChatbot

Requirements
- Windows/Linux only
- NVIDIA GPU
    check your CUDA version: nvcc -V # example versions: 11.1, 11.8, 12.1, etc.

Installation Guide

```bash
# 1. # Make sure your system has git, [conda](https://www.anaconda.com/docs/getting-started/miniconda/install), and FFmpeg installed. [HOW TO INSTALL FFMPEG](FFMPEGInstall.md)

# 2. Clone the code and prepare the environment 
git clone https://github.com/JasonZhai-9936/DarwinChatbot.git
cd DarwinChatbot

# 2. Run install_requirements.py to install all models
python3 install_requirements.py

# 3. Install remaining dependencies
pip install -r requirements.txt
```
