#generates pre-made videos from chunks

#1. enter chunks you want
#2. change outputdir to what you want

import subprocess
import os
import sys
import random
import glob
import shutil
import time

# === Config ===
CONDA_ENV = "LivePortrait"

# === USER CONFIGURATION - MODIFY THESE VALUES ===
# List of videos to process (without extension)
VIDEO_LIST = [ "clip10","clip7"]  


#VIDEO_LIST = ["clip1", "clip2","clip3","clip4","clip5","clip6",]  

# === Paths ===
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LivePortrait_DIR = os.path.join(REPO_DIR, "LivePortrait")
INFERENCE_SCRIPT = os.path.join(LivePortrait_DIR, "inference.py")
INPUT_IMAGE = os.path.join(LivePortrait_DIR, "assets", "prompts", "darwin_young.png")

# Output settings
OUTPUT_DIR = os.path.join(REPO_DIR, "stream", "talking_chunks")

# PKL directories
IDLE_PKL_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos", "pkls", "idle")
TALKING_PKL_DIR = os.path.join(REPO_DIR, "training", "idle_motion_videos", "pkls", "talking")

def run(command, cwd=None):
    print(f"[RUN] {' '.join(command) if isinstance(command, list) else command}")
    try:
        subprocess.run(command, cwd=cwd, shell=isinstance(command, str), check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def extract_last_frame(video_path, output_image_path):
    print(f"[INFO] Extracting last frame from {video_path} to {output_image_path}")
    command = f"ffmpeg -y -sseof -3 -i \"{video_path}\" -vframes 1 \"{output_image_path}\""
    run(command)

def get_next_chunk_number(output_dir):
    """
    Scan the output directory for existing chunk files and determine the next available number
    """
    existing_chunks = [
        f for f in os.listdir(output_dir)
        if f.startswith("chunk") and f.endswith(".mp4")
    ]

    existing_numbers = []
    for name in existing_chunks:
        try:
            number = int(name[len("chunk"):-len(".mp4")])
            existing_numbers.append(number)
        except ValueError:
            continue
    
    next_number = max(existing_numbers, default=0) + 1
    return next_number

def process_video_list():
    """
    Process the predefined list of video names and merge them in the end
    """
    temp_dir = os.path.join(OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    last_frame_image = os.path.join(temp_dir, "last_frame.png")
    current_input_image = INPUT_IMAGE
    
    generated_chunks = []
    
    print(f"[INFO] Processing {len(VIDEO_LIST)} specified videos")
    
    # Get the next available chunk number
    chunk_number = get_next_chunk_number(OUTPUT_DIR)
    print(f"[INFO] Will create chunk{chunk_number}.mp4")
    
    for i, video_name in enumerate(VIDEO_LIST, 1):
        print(f"\n[STEP] Processing video {i}/{len(VIDEO_LIST)}: {video_name}")
        
        # Determine if the video is in idle or talking directory
        idle_video_path = os.path.join(IDLE_PKL_DIR, f"{video_name}.pkl")
        talking_video_path = os.path.join(TALKING_PKL_DIR, f"{video_name}.pkl")
        
        if os.path.exists(idle_video_path):
            driving_video_path = idle_video_path
            print(f"[INFO] Found {video_name} in idle directory")
        elif os.path.exists(talking_video_path):
            driving_video_path = talking_video_path
            print(f"[INFO] Found {video_name} in talking directory")
        else:
            print(f"[WARNING] Video {video_name} not found in either directory. Skipping.")
            continue
        
        # Run inference
        run([
            "conda", "run", "-n", CONDA_ENV, "python", INFERENCE_SCRIPT,
            "-s", current_input_image,
            "-d", driving_video_path,
            "-o", temp_dir
        ])
        
        # Determine output filename
        driving_name = os.path.splitext(os.path.basename(driving_video_path))[0]
        input_name = os.path.splitext(os.path.basename(current_input_image))[0]
        output_filename = f"{input_name}--{driving_name}.mp4"
        output_chunk_path = os.path.join(temp_dir, output_filename)
        
        if not os.path.isfile(output_chunk_path):
            print(f"[ERROR] Expected output file not found: {output_chunk_path}")
            sys.exit(1)
            
        print(f"[INFO] Saved chunk as {output_chunk_path}")
        
        # Extract last frame for next iteration
        extract_last_frame(output_chunk_path, last_frame_image)
        current_input_image = last_frame_image
        
        generated_chunks.append(output_chunk_path)
    
    # Merge all chunks into final video
    if not generated_chunks:
        print("[ERROR] No videos were processed successfully")
        return
    
    print("\n[INFO] Merging all processed videos")
    final_output_name = f"chunk{chunk_number}.mp4"
    merged_output_path = os.path.join(OUTPUT_DIR, final_output_name)
    merge_list_path = os.path.join(temp_dir, f"merge_list_{chunk_number}.txt")
    
    with open(merge_list_path, "w") as f:
        for chunk_path in generated_chunks:
            rel_path = os.path.relpath(chunk_path, temp_dir)
            f.write(f"file '{rel_path}'\n")
    
    merge_cmd = (
        f"ffmpeg -y -f concat -safe 0 -i \"{merge_list_path}\" "
        f"-c:v copy -c:a aac -strict experimental \"{merged_output_path}\""
    )
    
    run(merge_cmd)
    
    if os.path.isfile(merged_output_path):
        print(f"[SUCCESS] Saved merged video as chunk{chunk_number}.mp4: {merged_output_path}")
    else:
        print("[ERROR] Failed to create merged video")
    
    # Clean up temp files
    print("\n[CLEANUP] Clearing temporary files")
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"[WARN] Failed to delete {file_path}: {e}")
    
    print("[CLEANUP] Done.")

if __name__ == "__main__":
    print(f"[INFO] Processing videos: {', '.join(VIDEO_LIST)}")
    print(f"[INFO] Output directory: {OUTPUT_DIR}")
    
    process_video_list()
    
    print("[COMPLETE] Processing finished")