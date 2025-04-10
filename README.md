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
**answer yes to "Do you wish to update your shell profile to automatically initialize conda?"

```bash
# 2. Clone the code and prepare the environment 
git clone https://github.com/JasonZhai-9936/DarwinChatbot.git
cd DarwinChatbot

# 3. Make a new miniconda environment
conda create -n DarwinChatbot python=3.12 -y
conda activate DarwinChatbot

# 4. Install base project dependencies
pip install -r requirements.txt

#5. Run the installation script:
python install_all.py

#OR

  a. python install_ollama_model.py
  b. python install_LivePortrait.py
  c. python install_latentsync.py
  d. python install_sparktts.py
  e. python move_assets.py

```

Quickstart 
```bash
# 1. Start env if not already open
conda activate DarwinChatbot

# 2. Run app.py
python ./scripts/app.py



```





#Additional tips for my partners if running into issues

# 1. 
- run app.py using:
python app.py
#instead of 
python3 app.y


# 2. If there's missing libraries, which there almost certainly will be, just conda activate the env and pip install it(and let me know)

# 3. /.install_flags tracks if each separate install component has already been run. 
#   If you're running into install issues, delete the /.install_flags folder

# 4. For miniconda install on linux, do:
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh


