# DarwinChatbot

Requirements
- Windows/Linux   
- NVIDIA GPU  
  Check your CUDA version:  
  ```bash
  nvcc -V  #To avoid issues, v12.4 is ideal, but slightly older and newer versions should also work
  ```

Installation Guide

1. Make sure your system has Git, [conda](https://www.anaconda.com/docs/getting-started/miniconda/install), and FFmpeg installed ([HOW TO INSTALL FFMPEG](FFMPEGInstall.md))

```bash
# 2. Clone the code and prepare the environment 
git clone https://github.com/JasonZhai-9936/DarwinChatbot.git
cd DarwinChatbot

# 3. Make a new miniconda environment
conda create -n LivePortrait python=3.12
conda activate LivePortrait

# 3. Run install_requirements.py to install all models in their own miniconda environments
python3 install_requirements.py

# 4. Install remaining dependencies
pip install -r requirements.txt


#Additional tips if running into issues

# 1. 
- run app.py using:
python app.py
#instead of 
python3 app.y


# 2. If there's missing libraries, which there likely may be, just conda activate the env and pip install it
```




