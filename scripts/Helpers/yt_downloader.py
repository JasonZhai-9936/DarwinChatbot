import os
import subprocess
import sys
import traceback

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def get_next_clip_number(save_dir):
    """Check for existing 'clipN.mp4' files in save_dir and return the next available clip number."""
    n = 1
    while os.path.exists(os.path.join(save_dir, f'clip{n}.mp4')):
        n += 1
    return n

def time_to_seconds(time_str):
    """Convert time string in format 'MM:SS' to seconds."""
    parts = time_str.split(':')
    if len(parts) == 2:
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    else:
        raise ValueError("Time format should be 'MM:SS'")

def download_and_splice_youtube(video_url, sections, save_dir):
    """
    Download YouTube video and splice it based on specified sections using yt-dlp.
    
    Parameters:
      video_url (str): URL of the YouTube video.
      sections (list of tuple): Each tuple should be (start_time, end_time) in 'MM:SS' format.
      save_dir (str): Directory where output clips will be saved.
    """
    # Ensure save directory exists
    ensure_directory_exists(save_dir)
    
    print(f"Downloading video from {video_url}")
    
    try:
        # Use yt-dlp to download the video
        temp_filename = "temp_downloaded_video.mp4"
        
        # Check if yt-dlp is installed
        try:
            subprocess.run(['yt-dlp', '--version'], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            print("yt-dlp is not installed. Please install it with 'pip install yt-dlp'")
            return
            
        # Download video with yt-dlp
        download_command = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '-o', temp_filename,
            video_url
        ]
        print(f"Running: {' '.join(download_command)}")
        subprocess.run(download_command, check=True)
        print("Download complete!")
        
        # Process each section
        clip_number = get_next_clip_number(save_dir)
        for start_str, end_str in sections:
            # Convert time strings to seconds
            start = time_to_seconds(start_str)
            end = time_to_seconds(end_str)
            
            duration = end - start
            output_filename = os.path.join(save_dir, f'clip{clip_number}.mp4')
            
            # Build the ffmpeg command - FIXED VERSION using simplified encoding
            # Using a simpler approach that should work with most FFmpeg installations
            # Method 1: First seeking, then extracting - better for accuracy
            command = [
                'ffmpeg',
                '-ss', str(start),  # Seek before input for more accurate starting point
                '-i', temp_filename,
                '-t', str(duration),
                '-q:v', '2',  # Use basic quality setting (0-31, 2 is high quality)
                '-q:a', '2',  # Audio quality
                '-vf', 'format=yuv420p',  # Ensure compatibility
                output_filename
            ]
            print(f"Running: {' '.join(command)}")
            subprocess.run(command, check=True)
            print(f"Created clip: {output_filename}")
            clip_number += 1
        
        # Clean up the temporary file
        os.remove(temp_filename)
        print("Temporary file removed. Process complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()  # More detailed error information

# Example usage
if __name__ == "__main__":
    # Specify your YouTube URL here
    video_url = "https://www.youtube.com/watch?v=D46dnKLyE8I"
    
    # Save directory relative to /scripts location
    save_dir = os.path.join("training", "idle_motion_videos", "talking_videos")
    
    # Specify your time sections here
    sections_to_extract = [
        ('0:10', '0:20'), 
        ('0:30', '0:40'), ('0:45', '0:55'),('0:15', '0:25'),
        ('2:38', '2:48'), 
        ('4:18', '4:28'), 
        ('5:25', '5:35'), 
        ('5:54', '6:04')
    ]
    
    if sections_to_extract:
        print(f"Processing {len(sections_to_extract)} sections...")
        download_and_splice_youtube(video_url, sections_to_extract, save_dir)
    else:
        print("No time sections provided. Exiting.")