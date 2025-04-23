#!/usr/bin/env python
# Copyright (c) 2025 
#
# Script to run Spark-TTS inference with appropriate parameters

import os
import sys
import glob
import subprocess
import re
import argparse
from typing import Optional

# === Config ===
CONDA_ENV = "SparkTTS"

def get_next_speech_number(speech_dir):
    """Find the highest numbered speech file and return the next number."""
    speech_files = glob.glob(os.path.join(speech_dir, "speech*.wav"))
    if not speech_files:
        return 1
    
    # Extract numbers from filenames
    numbers = []
    for file in speech_files:
        match = re.search(r'speech(\d+)\.wav', os.path.basename(file))
        if match:
            numbers.append(int(match.group(1)))
    
    if numbers:
        return max(numbers) + 1
    return 1

def run(command, cwd=None, shell=False, fail_hard=False):
    """
    Runs a subprocess command.
    - shell: True if command is a string; False for list-style command
    - fail_hard: If True, raises error on failure; else logs and returns False
    Returns: True on success, False on failure
    """
    cmd_str = command if isinstance(command, str) else ' '.join(command)
    print(f"[RUN] {cmd_str}")

    try:
        subprocess.run(command, cwd=cwd, shell=shell or isinstance(command, str), check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}")
        if fail_hard:
            raise
        return False

def run_tts(
    text: str,
    device: str = "0",
    model_dir: str = "pretrained_models/Spark-TTS-0.5B",
    prompt_text: str = "Their pointed heads and short dorsal fins.",
    prompt_speech_path: str = "example/DavidA2.mp3"
) -> str:
    """
    Run Spark-TTS inference and return the path to the generated audio file.
    
    Args:
        text: The text to synthesize
        device: GPU device to use
        model_dir: Directory containing the model
        prompt_text: Prompt text for the TTS model
        prompt_speech_path: Path to the prompt speech file
        
    Returns:
        Path to the generated audio file
    """
    # Script is always in /scripts, so get the repo root by going up one level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    spark_tts_dir = os.path.join(repo_root, "Spark-TTS")
    speech_dir = os.path.join(repo_root, "stream", "speech")
    
    # Ensure the speech directory exists
    os.makedirs(speech_dir, exist_ok=True)
    
    # Get the next speech file number
    next_num = get_next_speech_number(speech_dir)
    output_filename = f"speech{next_num}.wav"
    save_path = os.path.join(speech_dir, output_filename)
    
    # Create the command as a string instead of a list for better shell handling
    # The conda environment needs to be activated via shell command
    conda_command = f"conda run -n {CONDA_ENV} python -m cli.inference " + \
                   f"--text \"{text}\" " + \
                   f"--device {device} " + \
                   f"--save_dir \"{speech_dir}\" " + \
                   f"--model_dir \"{model_dir}\" " + \
                   f"--prompt_text \"{prompt_text}\" " + \
                   f"--prompt_speech_path \"{prompt_speech_path}\""
    
    # Run the command
    print(f"[TTS] Running inference, output will be saved to {speech_dir}")
    success = run(conda_command, cwd=spark_tts_dir, shell=True)
    
    # After running, find the latest WAV file in the speech dir
    speech_files = glob.glob(os.path.join(speech_dir, "*.wav"))
    if speech_files:
        latest_speech = max(speech_files, key=os.path.getctime)
        
        # Rename the file to our sequential naming format if needed
        if os.path.basename(latest_speech) != output_filename:
            new_path = os.path.join(speech_dir, output_filename)
            try:
                os.rename(latest_speech, new_path)
                print(f"[INFO] Renamed {os.path.basename(latest_speech)} to {output_filename}")
                latest_speech = new_path
            except Exception as e:
                print(f"[WARN] Failed to rename speech file: {e}")
        
        print(f"[SUCCESS] TTS file created: {latest_speech}")
        return latest_speech
    
    # If no speech file was found, create a dummy file for testing
    if not success:
        print(f"[FALLBACK] Creating dummy speech file at {save_path}")
        # Create an empty file
        with open(save_path, 'w') as f:
            f.write('')
        return save_path
        
    print(f"[ERROR] No speech file was found in {speech_dir}")
    return ""

def main():
    parser = argparse.ArgumentParser(description="Run Spark-TTS inference")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--device", default="0", help="GPU device to use")
    parser.add_argument("--model_dir", default="pretrained_models/Spark-TTS-0.5B", 
                       help="Directory containing the model")
    parser.add_argument("--prompt_text", 
                       default="Antartic Minke Whales. Their pointed heads and short dorsal fins give them speed and endurance.",
                       help="Prompt text for the TTS model")
    parser.add_argument("--prompt_speech_path", default="example/DavidA2.mp3",
                       help="Path to the prompt speech file")
    
    args = parser.parse_args()
    
    # Call the main function with parsed arguments
    output_path = run_tts(
        text=args.text,
        device=args.device,
        model_dir=args.model_dir,
        prompt_text=args.prompt_text,
        prompt_speech_path=args.prompt_speech_path
    )
    
    # Return appropriate exit code
    return 0 if output_path else 1

if __name__ == "__main__":
    sys.exit(main())