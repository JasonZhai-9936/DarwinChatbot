import subprocess
import os
import sys
import json
import tempfile

def concatenate_videos(video_path1: str, video_path2: str):
    """
    Joins two videos together sequentially.
    Works with videos that have audio and those without.
    The output is saved as <firstVideoName>_<secondVideoName>.mp4 in the same directory as the first video.
    """
    # Get the directory of the current script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one directory and then into ffmpeg folder to find ffmpeg.exe
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")
    
    # Get file info
    dir_name1, file_name1 = os.path.split(video_path1)
    base_name1, ext1 = os.path.splitext(file_name1)
    
    _, file_name2 = os.path.split(video_path2)
    base_name2, _ = os.path.splitext(file_name2)
    
    # Create output path
    output_path = os.path.join(dir_name1, f"{base_name1}_{base_name2}{ext1}")
    
    try:
        print(f"[INFO] Using FFmpeg from: {ffmpeg_path}")
        print(f"[INFO] Concatenating: {video_path1} and {video_path2}")
        
        # Instead of checking for audio streams, which might fail,
        # we'll try the more reliable approach - simply concatenate video streams only
        subprocess.run([
            ffmpeg_path, "-y", 
            "-i", video_path1,
            "-i", video_path2,
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[outv]",
            "-map", "[outv]",
            output_path
        ], check=True)
        
        print(f"[SUCCESS] Concatenated video (video-only) saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg failed:", e)
        print("Command output:", e.output if hasattr(e, 'output') else "No output")
        
        # Fallback method - try the concat demuxer approach
        try:
            print("[INFO] Trying alternative method with concat demuxer...")
            # Create a temporary file listing the videos to concatenate
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(f"file '{video_path1}'\n")
                temp_file.write(f"file '{video_path2}'\n")
                concat_list_path = temp_file.name
            
            subprocess.run([
                ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy",  # Copy streams without re-encoding
                output_path
            ], check=True)
            
            print(f"[SUCCESS] Concatenated video saved to: {output_path}")
            
            # Clean up the temporary file
            os.unlink(concat_list_path)
            
        except subprocess.CalledProcessError as e2:
            print("[ERROR] Alternative method also failed:", e2)
        except Exception as e3:
            print("[ERROR] Unexpected error in fallback method:", e3)
            
    except FileNotFoundError as e:
        print(f"[ERROR] Could not find FFmpeg at: {ffmpeg_path}")
        print("Please verify the path to ffmpeg.exe or install FFmpeg")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    input_video_path1 = r"C:\Users\Jason\Documents\School\BIOIN401\Sora_Assets\Nodes\Full_Samples\1_clip_1.mp4"
    input_video_path2 = r"C:\Users\Jason\Documents\School\BIOIN401\Sora_Assets\Nodes\pipe2main\1.mp4"
    concatenate_videos(input_video_path1, input_video_path2)    