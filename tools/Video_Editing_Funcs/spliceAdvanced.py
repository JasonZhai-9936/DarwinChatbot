import subprocess
import os
import sys

def extract_video_clip(video_path: str, start_time: str, end_time: str, quality='high'):
    """
    Extracts a clip from a video between the specified start and end times.
    Times should be in the format 'HH:MM:SS' or 'MM:SS' or seconds as a string.
    
    Parameters:
        video_path (str): Path to the input video file
        start_time (str): Start time of the clip
        end_time (str): End time of the clip
        quality (str): Quality setting - 'high', 'medium', or 'fast'
        
    The output is saved as <originalName>_clip.mp4 in the same directory.
    """
    # Get the directory of the current script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one directory and then into ffmpeg folder to find ffmpeg.exe
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")
    
    # Get file info
    dir_name, file_name = os.path.split(video_path)
    base_name, ext = os.path.splitext(file_name)
    
    # Create output path
    output_path = os.path.join(dir_name, f"{base_name}_clip{ext}")
    
    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Extracting clip from '{start_time}' to '{end_time}' from video: {video_path}")
        
        # First, try to get information about the video
        probe_cmd = [
            ffmpeg_path, 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            video_path
        ]
        
        # Get video duration to check if timestamps are valid
        try:
            duration = float(subprocess.check_output(probe_cmd, universal_newlines=True).strip())
            print(f"[INFO] Video duration: {duration} seconds")
        except subprocess.CalledProcessError:
            print("[WARNING] Could not determine video duration")
            duration = None
        
        # Set encoding parameters based on quality
        if quality == 'high':
            # High quality, slower encoding
            video_params = ["-c:v", "libx264", "-preset", "slow", "-crf", "18"]
            audio_params = ["-c:a", "aac", "-b:a", "192k"]
        elif quality == 'medium':
            # Balanced quality and speed
            video_params = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]
            audio_params = ["-c:a", "aac", "-b:a", "128k"]
        else:  # 'fast'
            # Faster encoding, lower quality
            video_params = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28"]
            audio_params = ["-c:a", "aac", "-b:a", "96k"]
        
        # Build the FFmpeg command
        # For accurate seeking, use -ss before -i for fast seeking
        # but also include -ss after -i for frame-accurate cutting
        cmd = [
            ffmpeg_path, "-y",
            "-ss", start_time,  # Seek before input (fast)
            "-i", video_path,
            "-ss", "0",  # Fine-tune from the seek position
            "-to", end_time if ":" in end_time else 
                  (str(float(end_time) - float(start_time.replace(":", "."))) 
                   if ":" not in start_time else end_time),
        ]
        
        # Add encoding parameters
        cmd.extend(video_params)
        cmd.extend(audio_params)
        
        # Additional parameters for larger videos
        cmd.extend([
            "-vsync", "vfr",  # Variable framerate for better sync
            "-movflags", "+faststart",  # Web optimization
            output_path
        ])
        
        print(f"[INFO] Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        print(f"[SUCCESS] Extracted clip saved to: {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg command failed: {e}")
        
        # More aggressive fallback for very problematic videos
        try:
            print("[INFO] Trying alternative keyframe-agnostic method...")
            
            fallback_cmd = [
                ffmpeg_path, "-y",
                "-ss", start_time,
                "-i", video_path,
                "-ss", "0",
                "-to", end_time if ":" in end_time else 
                      (str(float(end_time) - float(start_time.replace(":", "."))) 
                       if ":" not in start_time else end_time),
                "-c:v", "libx264", "-preset", "ultrafast",
                "-tune", "fastdecode",
                "-g", "1",  # Force keyframes at every frame
                "-keyint_min", "1",
                "-c:a", "aac",
                "-b:a", "128k",
                "-vsync", "1",  # Force sync
                output_path
            ]
            
            print(f"[INFO] Running fallback command: {' '.join(fallback_cmd)}")
            subprocess.run(fallback_cmd, check=True)
            
            print(f"[SUCCESS] Extracted clip (fallback method) saved to: {output_path}")
            
        except subprocess.CalledProcessError as e2:
            print(f"[ERROR] Alternative method also failed: {e2}")
            
    except FileNotFoundError as e:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")
        print("Please verify the path to ffmpeg.exe or install FFmpeg")
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        

if __name__ == "__main__":
    input_video_path = r"C:\Users\Jason\Downloads\sailing.mp4"
    
    # Define start and end times here (in format 'HH:MM:SS' or 'MM:SS' or seconds)
    start_time = "00:15:10"
    end_time = "00:15:17"
    
    # 'high' for best quality, 'medium' for balanced, 'fast' for speed
    extract_video_clip(input_video_path, start_time, end_time, quality='high')