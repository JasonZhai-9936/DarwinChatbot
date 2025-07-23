import os
import subprocess
import yt_dlp
import time

def download_youtube_snippet(url, start_time, end_time, output_filename="youtube_snippet.mp4"):
    """
    Download a YouTube video and extract a clip between specific timestamps.
    Uses 1080p quality when available.
    
    Args:
        url (str): YouTube video URL
        start_time (str): Start time in format "HH:MM:SS" or "MM:SS" or seconds as int
        end_time (str): End time in format "HH:MM:SS" or "MM:SS" or seconds as int
        output_filename (str): Name of the output file
    
    Returns:
        str: Path to the downloaded snippet
    """
    # Get script location and FFmpeg path
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_path = os.path.join(os.path.dirname(current_script_dir), "ffmpeg", "ffmpeg.exe")
    
    # Ensure directory exists for output file
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a temporary filename for the full video
    temp_dir = os.path.dirname(output_filename) or "."
    timestamp = int(time.time())
    temp_filename = os.path.join(temp_dir, f"temp_youtube_video_{timestamp}.mp4")
    
    try:
        # Step 1: Download the full video in 1080p when available
        ydl_opts = {
            'format': 'best[height=1080][ext=mp4]/best[height<=1080][ext=mp4]/best',  # Prefer 1080p
            'outtmpl': temp_filename,
            'noplaylist': True,
        }
        
        print(f"Downloading video from: {url}")
        print("Requesting 1080p quality if available...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Get available formats
            formats = info.get('formats', [])
            best_1080p = None
            for f in formats:
                height = f.get('height')
                if height == 1080 and f.get('ext') == 'mp4':
                    best_1080p = f.get('format_id')
                    break
            
            if best_1080p:
                print(f"Found 1080p format: {best_1080p}")
                ydl_opts['format'] = best_1080p
            else:
                print("1080p not available, using best available quality")
            
            # Download the video
            ydl.download([url])
        
        print(f"Video downloaded to: {temp_filename}")
        
        # Step 2: Extract the clip with re-encoding to ensure playability
        print(f"Extracting clip from {start_time} to {end_time}")
        
        # ALWAYS use re-encoding approach for reliability
        subprocess.run([
            ffmpeg_path, "-y",
            "-ss", start_time,  # Start time
            "-to", end_time,    # End time
            "-i", temp_filename,  # Input file
            "-c:v", "libx264",  # Re-encode video with H.264
            "-c:a", "aac",      # Re-encode audio with AAC
            "-preset", "fast",  # Balance speed and quality
            "-crf", "18",       # Higher quality (lower value = better quality)
            output_filename
        ], check=True)
        
        print(f"Clip extracted and saved to: {output_filename}")
        return output_filename
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
                print("Temporary video file removed")
            except:
                print("Could not remove temporary file")


if __name__ == "__main__":
    # Set your YouTube URL, start time, and end time here
    url = "https://www.youtube.com/watch?v=rFRuO_M9Fdw"
    clip_start = "00:15:10"
    clip_end = "00:15:17"
    save_path = "sailing near Tierra del Fuego.mp4"
    
    # Download the snippet
    output_file = download_youtube_snippet(url, clip_start, clip_end, save_path)
    print(f"Video snippet saved as: {output_file}")