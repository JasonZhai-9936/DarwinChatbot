import subprocess
import os

def crop_to_480x720(video_path: str):
    """
    Crops the input video to 480x720 (portrait 2:3 aspect ratio) centered.
    Assumes FFmpeg is located in ../ffmpeg/ffmpeg.exe relative to this script.
    """
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")

    dir_name, file_name = os.path.split(video_path)
    base_name, ext = os.path.splitext(file_name)

    output_path = os.path.join(dir_name, f"{base_name}_Cropped{ext}")

    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Cropping: {video_path} to 480x720")

        subprocess.run([
            ffmpeg_path, "-y", "-i", video_path,
            "-vf", "crop=480:720:(in_w-480)/2:(in_h-720)/2",
            "-c:a", "copy",
            output_path
        ], check=True)

        print(f"[SUCCESS] Cropped video saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg command failed:", e)
    except FileNotFoundError as e:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")
        print("Please verify the path to ffmpeg.exe or install FFmpeg")

if __name__ == "__main__":
    input_video_path = r"C:\Users\Jason\Documents\DarwinChatbot\stream\Nodes\standingMansion2standingMansion\pourdrink.mp4"
    crop_to_480x720(input_video_path)
