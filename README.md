# DarwinChatbot

Requirements
- Windows/Linux   
- NVIDIA GPU  
  Check your CUDA version:  
  ```bash
  nvcc -V  #To avoid issues, v12.6 is ideal, but any v12.x should work. 11.8 may also work
  ```

Installation Guide

1. Make sure your system has Git, [conda](https://www.anaconda.com/docs/getting-started/miniconda/install), and FFmpeg installed ([HOW TO INSTALL FFMPEG](FFMPEGInstall.md))

```bash
# 2. Clone the code and prepare the environment 
git clone https://github.com/JasonZhai-9936/DarwinChatbot.git
cd DarwinChatbot

# 3. Make a new miniconda environment
conda create -n DarwinChatbot python=3.12
conda activate DarwinChatbot

# 3. Run install_requirements.py to install all models in their own miniconda environments
python3 install_requirements.py

# 4. Install remaining dependencies
pip install -r requirements.txt


<<<<<<< HEAD
#Additional tips for my partners if running into issues
=======
#Additional tips if running into issues
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3

# 1. 
- run app.py using:
python app.py
#instead of 
python3 app.y


<<<<<<< HEAD
# 2. If there's missing libraries, which there almost certainly will be, just conda activate the env and pip install it(and let me know)

# 3. /.install_flags tracks if each separate install component has already been run. 
#   If you're running into install issues, delete the /.install_flags folder
=======
# 2. If there's missing libraries, which there likely may be, just conda activate the env and pip install it
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
```



Quickstart 
```bash
# 1. Start env if not already open
conda activate DarwinChatbot

# 2. Run app.py
python app.py



```


