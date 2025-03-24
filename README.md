# DarwinChatbot

Requirements
- Windows/Linux   
- NVIDIA GPU  
  Check your CUDA version:  
  ```bash
  nvcc -V  #To avoid issues, v12.4 is ideal, but older and newer versions shoudl also work
  ```

Installation Guide

1. Make sure your system has Git, [conda](https://www.anaconda.com/docs/getting-started/miniconda/install), and FFmpeg installed ([HOW TO INSTALL FFMPEG](FFMPEGInstall.md))

```bash
# 2. Clone the code and prepare the environment 
git clone https://github.com/JasonZhai-9936/DarwinChatbot.git
cd DarwinChatbot

# 3. Run install_requirements.py to install all models 
python3 install_requirements.py

# 4. Install remaining dependencies
pip install -r requirements.txt
```
