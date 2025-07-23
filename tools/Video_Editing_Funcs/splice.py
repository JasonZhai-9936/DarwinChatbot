import subprocess
import os
import sys

def extract_video_clip(video_path: str, start_time: str, end_time: str):
    """
    Extracts a clip from a video between the specified start and end times.
    Times should be in the format 'HH:MM:SS' or 'MM:SS' or seconds as a string.
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
        
        # Use the -ss (start time) and -to (end time) parameters for precise extraction
        subprocess.run([
            ffmpeg_path, "-y",
            "-ss", start_time,  # Start time
            "-to", end_time,    # End time
            "-i", video_path,   # Input file
            "-c", "copy",       # Copy streams without re-encoding for speed
            output_path
        ], check=True)
        
        print(f"[SUCCESS] Extracted clip saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg failed:", e)
        
        # Fallback method with re-encoding if stream copy fails
        try:
            print("[INFO] Trying alternative method with re-encoding...")
            subprocess.run([
                ffmpeg_path, "-y",
                "-ss", start_time,
                "-to", end_time,
                "-i", video_path,
                "-c:v", "libx264",  # Re-encode video with H.264
                "-c:a", "aac",      # Re-encode audio with AAC
                output_path
            ], check=True)
            
            print(f"[SUCCESS] Extracted clip (re-encoded) saved to: {output_path}")
            
        except subprocess.CalledProcessError as e2:
            print("[ERROR] Alternative method also failed:", e2)
            
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
    
    extract_video_clip(input_video_path, start_time, end_time)