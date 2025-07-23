import subprocess
import os
import sys

def create_video_loop(video_path: str):
    """
    Creates a seamless forward + reverse loop of the input video.
    The output is saved as <originalName>Loop.mp4 in the same directory.
    """
    # Get the directory of the current script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one directory and then into ffmpeg folder to find ffmpeg.exe
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")
    
    dir_name, file_name = os.path.split(video_path)
    base_name, ext = os.path.splitext(file_name)

    reversed_path = os.path.join(dir_name, f"{base_name}_reversed{ext}")
    output_path = os.path.join(dir_name, f"{base_name}Loop{ext}")

    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Reversing: {video_path}")
        subprocess.run([
            ffmpeg_path, "-y", "-i", video_path,
            "-vf", "reverse", "-an",
            reversed_path
        ], check=True)

        print("[INFO] Concatenating original and reversed videos")
        subprocess.run([
            ffmpeg_path, "-y",
            "-i", video_path,
            "-i", reversed_path,
            "-filter_complex", "[0:v:0][1:v:0]concat=n=2:v=1:a=0[outv]",
            "-map", "[outv]",
            output_path
        ], check=True)

        print(f"[SUCCESS] Looped video saved to: {output_path}")

        # Optionally delete the reversed video
        os.remove(reversed_path)

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg failed:", e)
    except FileNotFoundError as e:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")
        print("Please verify the path to ffmpeg.exe or install FFmpeg")

if __name__ == "__main__":
    input_video_path = r"C:\Users\Jason\Documents\DarwinChatbot\stream\Nodes\HMS_Beagle_854_256_07.gif"
    create_video_loop(input_video_path) 