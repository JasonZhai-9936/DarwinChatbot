import subprocess
import os
import sys

def slow_down_video(video_path: str, speed_factor: float = 0.8):
    """
    Adjusts video playback speed by modifying the video frame timing only (ignores audio).
    For slow motion, use speed_factor < 1.0. For fast motion, use speed_factor > 1.0.
    Output is saved as <originalName>Slow.mp4 in the same directory.
    """
    # Get the directory of the current script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one directory and then into ffmpeg folder to find ffmpeg.exe
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")
    
    if not os.path.exists(video_path):
        print(f"[ERROR] Input video not found at: {video_path}")
        return

    dir_name, file_name = os.path.split(video_path)
    base_name, ext = os.path.splitext(file_name)

    output_path = os.path.join(dir_name, f"{base_name}Slow{ext}")
    tempo = 1 / speed_factor

    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Adjusting video speed by factor {speed_factor} (setpts={tempo}*PTS)")
        
        subprocess.run([
            ffmpeg_path, "-y", "-i", video_path,
            "-an",  # strip audio entirely
            "-vf", f"setpts={tempo}*PTS",
            output_path
        ], check=True)

        print(f"[SUCCESS] Adjusted video saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg failed:", e)
    except FileNotFoundError:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")

if __name__ == "__main__":
    input_video_path = r"C:\Users\Jason\Documents\DarwinChatbot\stream\Nodes\HMS-Beagle.mp4"
    slow_down_video(input_video_path, speed_factor=1.9)  # Use >1.0 to speed up
