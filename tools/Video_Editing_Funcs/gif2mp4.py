import subprocess
import os
import sys

def create_video_loop(gif_path: str):
    """
    Converts a GIF to MP4 format using FFmpeg.
    The output is saved as <originalName>.mp4 in the same directory.
    """
    # Get the directory of the current script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up one directory and then into ffmpeg folder to find ffmpeg.exe
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")

    dir_name, file_name = os.path.split(gif_path)
    base_name, _ = os.path.splitext(file_name)

    output_path = os.path.join(dir_name, f"{base_name}.mp4")

    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Converting GIF to MP4: {gif_path}")
        subprocess.run([
            ffmpeg_path, "-y", "-i", gif_path,
            "-movflags", "faststart", "-pix_fmt", "yuv420p", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            output_path
        ], check=True)

        print(f"[SUCCESS] Converted MP4 saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg failed:", e)
    except FileNotFoundError:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")
        print("Please verify the path to ffmpeg.exe or install FFmpeg")

if __name__ == "__main__":
    input_gif_path = r"C:\Users\Jason\Downloads\map-voyage-Charles-Darwin-HMS-Beagle.webp"
    create_video_loop(input_gif_path)
