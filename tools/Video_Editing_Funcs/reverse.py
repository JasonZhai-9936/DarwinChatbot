import subprocess
import os
import sys

def reverse_video(video_path: str):
    """
    Creates a reversed version of the input video.
    The output is saved as <originalName>Reversed.mp4 in the same directory.
    """
    # Get the directory of the current script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one directory and then into ffmpeg folder to find ffmpeg.exe
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")
    
    dir_name, file_name = os.path.split(video_path)
    base_name, ext = os.path.splitext(file_name)

    output_path = os.path.join(dir_name, f"{base_name}Reversed{ext}")

    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Reversing: {video_path}")
        
        # Apply the reverse filter to create the reversed video
        subprocess.run([
            ffmpeg_path, "-y", "-i", video_path,
            "-vf", "reverse", "-an",  # Apply reverse filter, remove audio
            output_path
        ], check=True)

        print(f"[SUCCESS] Reversed video saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg failed:", e)
    except FileNotFoundError as e:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")
        print("Please verify the path to ffmpeg.exe or install FFmpeg")

if __name__ == "__main__":
    input_video_path = r"C:\Users\Jason\Documents\DarwinChatbot\stream\Nodes\HMS_Beagle_854_256_07.gif"
    reverse_video(input_video_path)