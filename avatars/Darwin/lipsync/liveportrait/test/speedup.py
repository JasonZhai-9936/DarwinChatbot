import os
import subprocess
from pathlib import Path

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 
            'format=duration', '-of', 'csv=p=0', str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        print(f"Error getting duration for {video_path}")
        return None

def speed_up_video(input_path, output_path, target_duration=0.2):
    """Speed up video to target duration with highest quality"""
    original_duration = get_video_duration(input_path)
    
    if original_duration is None:
        return False
    
    # Calculate speed factor
    speed_factor = original_duration / target_duration
    
    print(f"Processing {input_path.name}: {original_duration:.2f}s → {target_duration}s (speed: {speed_factor:.2f}x)")
    
    # FFmpeg command for highest quality speed-up
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-filter:v', f'setpts={1/speed_factor}*PTS',  # Video speed
        '-filter:a', f'atempo={min(speed_factor, 2)}',  # Audio speed (max 2x per filter)
        '-c:v', 'libx264',  # High quality video codec
        '-preset', 'slow',  # Highest quality preset
        '-crf', '18',  # Very high quality (lower = better, 18 is near-lossless)
        '-c:a', 'aac',  # High quality audio codec
        '-b:a', '320k',  # High bitrate audio
        '-y',  # Overwrite output
        str(output_path)
    ]
    
    # Handle audio speed > 2x (FFmpeg limitation - need multiple atempo filters)
    if speed_factor > 2:
        atempo_filters = []
        remaining_speed = speed_factor
        while remaining_speed > 2:
            atempo_filters.append('atempo=2')
            remaining_speed /= 2
        atempo_filters.append(f'atempo={remaining_speed}')
        
        # Update command with multiple atempo filters
        audio_filter = ','.join(atempo_filters)
        cmd[cmd.index('-filter:a') + 1] = audio_filter
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error processing {input_path.name}: {e}")
        return False

def process_directory(directory_path, target_duration=0.2, backup_suffix="_original"):
    """Process all video files in directory, replacing originals"""
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Directory {directory_path} does not exist")
        return
    
    # Common video extensions
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    
    video_files = [
        f for f in directory.iterdir() 
        if f.is_file() and f.suffix.lower() in video_extensions
        and not f.stem.endswith(backup_suffix)  # Skip backup files
    ]
    
    if not video_files:
        print(f"No video files found in {directory_path}")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    processed = 0
    skipped = 0
    failed = 0
    
    for video_file in video_files:
        original_duration = get_video_duration(video_file)
        
        if original_duration is None:
            print(f"Error reading {video_file.name}, skipping")
            failed += 1
            continue
            
        if original_duration <= target_duration:
            print(f"Skipping {video_file.name} - already {original_duration:.2f}s (≤ {target_duration}s)")
            skipped += 1
            continue
        
        # Create temporary output file
        temp_file = video_file.parent / f"{video_file.stem}_temp{video_file.suffix}"
        
        # Process video
        result = speed_up_video(video_file, temp_file, target_duration)
        
        if result:
            # Create backup of original
            backup_file = video_file.parent / f"{video_file.stem}{backup_suffix}{video_file.suffix}"
            
            try:
                # Rename original to backup
                video_file.rename(backup_file)
                # Rename temp to original name
                temp_file.rename(video_file)
                print(f"✓ Replaced {video_file.name} (backup saved as {backup_file.name})")
                processed += 1
            except OSError as e:
                print(f"✗ Error replacing {video_file.name}: {e}")
                # Clean up temp file if it exists
                if temp_file.exists():
                    temp_file.unlink()
                failed += 1
        else:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            failed += 1
    
    print(f"\nSummary:")
    print(f"Processed: {processed}")
    print(f"Skipped (already short): {skipped}")
    print(f"Failed: {failed}")
    if processed > 0:
        print(f"Original files backed up with '{backup_suffix}' suffix")

# Usage
if __name__ == "__main__":
    # Set your directory path here
    directory_path = "."  # Current directory, change as needed
    target_duration = 0.2  # Target duration in seconds
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: FFmpeg and FFprobe are required but not found in PATH")
        print("Please install FFmpeg: https://ffmpeg.org/download.html")
        exit(1)
    
    process_directory(directory_path, target_duration)