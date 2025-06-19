import subprocess
import os
import sys
from pathlib import Path

def check_ffmpeg():
    """Check if ffmpeg is available and return the path."""
    print("🔍 Checking FFmpeg availability...")
    
    # Try different ways to find ffmpeg
    ffmpeg_paths = [    
        'ffmpeg',  # In PATH
        'ffmpeg.exe',  # Windows with extension
        r'C:\ffmpeg\ffmpeg\bin\ffmpeg.exe',  # Common path
        r'C:\ffmpeg\bin\ffmpeg.exe',  # Alternative path
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',  # Program Files
    ]
    
    for ffmpeg_path in ffmpeg_paths:
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg found: {version_line}")
                return ffmpeg_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        except Exception as e:
            print(f"Error checking {ffmpeg_path}: {e}")
            continue
    
    print("❌ FFmpeg not found!")
    print("Please install FFmpeg: https://ffmpeg.org/download.html")
    return None

def get_audio_info(audio_path, ffmpeg_path='ffmpeg'):
    """Get audio file information using ffprobe."""
    ffprobe_paths = [
        ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe'),
        ffmpeg_path.replace('ffmpeg', 'ffprobe'),
        'ffprobe.exe',
        'ffprobe'
    ]
    
    for ffprobe_path in ffprobe_paths:
        try:
            cmd = [
                ffprobe_path, '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            duration = float(result.stdout.strip())
            return {'duration': duration}
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
            continue
    
    print("⚠️  Could not get audio duration (ffprobe not available)")
    return None

def slow_down_audio(input_path, output_path, slowdown_factor, ffmpeg_path='ffmpeg'):
    """
    Slow down audio by a given factor while maintaining pitch.
    
    Args:
        input_path (str): Path to input audio file
        output_path (str): Path to output audio file
        slowdown_factor (float): Factor to slow down (e.g., 2.0 = half speed, 1.5 = 2/3 speed)
        ffmpeg_path (str): Path to ffmpeg executable
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return False
    
    if slowdown_factor <= 0:
        print(f"❌ Invalid slowdown factor: {slowdown_factor}")
        return False
    
    # Get original audio info
    audio_info = get_audio_info(input_path, ffmpeg_path)
    if audio_info:
        original_duration = audio_info['duration']
        new_duration = original_duration * slowdown_factor
        print(f"📊 Original duration: {original_duration:.2f}s")
        print(f"📊 New duration: {new_duration:.2f}s")
        print(f"📊 Slowdown factor: {slowdown_factor:.2f}x")
    
    # Build FFmpeg command for high-quality audio slowdown
    # Using atempo filter (preserves pitch) - need to chain multiple filters for >2x slowdown
    if slowdown_factor > 2.0:
        # Need multiple atempo filters since each can only slow down max 2x
        print("🔧 Using multiple atempo filters for >2x slowdown...")
        
        atempo_filters = []
        remaining_factor = slowdown_factor
        
        while remaining_factor > 2.0:
            atempo_filters.append('atempo=0.5')  # Each filter slows by 2x
            remaining_factor /= 2.0
        
        # Add final filter for remaining slowdown
        final_atempo = 1.0 / remaining_factor
        atempo_filters.append(f'atempo={final_atempo:.6f}')
        
        audio_filter = ','.join(atempo_filters)
        print(f"🔧 Audio filter chain: {audio_filter}")
        
    else:
        # Single atempo filter for ≤2x slowdown
        atempo_value = 1.0 / slowdown_factor
        audio_filter = f'atempo={atempo_value:.6f}'
        print(f"🔧 Audio filter: {audio_filter}")
    
    # High-quality FFmpeg command
    cmd = [
        ffmpeg_path, '-i', input_path,
        '-filter:a', audio_filter,
        '-c:a', 'libmp3lame',  # High quality MP3 encoder
        '-b:a', '320k',        # High bitrate
        '-y', output_path
    ]
    
    # Alternative high-quality options based on output format
    output_ext = Path(output_path).suffix.lower()
    if output_ext in ['.wav', '.flac']:
        # Lossless output
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-filter:a', audio_filter,
            '-c:a', 'pcm_s16le' if output_ext == '.wav' else 'flac',
            '-y', output_path
        ]
    elif output_ext in ['.m4a', '.aac']:
        # AAC output
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-filter:a', audio_filter,
            '-c:a', 'aac',
            '-b:a', '320k',
            '-y', output_path
        ]
    
    print(f"🎵 Slowing down audio...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        
        # Verify output file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Audio slowed down successfully!")
            print(f"📁 Output: {output_path} ({file_size:,} bytes)")
            
            # Verify new duration if possible
            new_info = get_audio_info(output_path, ffmpeg_path)
            if new_info:
                actual_duration = new_info['duration']
                print(f"📊 Actual new duration: {actual_duration:.2f}s")
                if audio_info:
                    actual_factor = actual_duration / audio_info['duration']
                    print(f"📊 Actual slowdown factor: {actual_factor:.2f}x")
            
            return True
        else:
            print(f"❌ Output file was not created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error:")
        print(f"   Return code: {e.returncode}")
        print(f"   Error output: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ Process timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def slow_down_audio_precise_tempo(input_path, output_path, new_tempo_bpm, ffmpeg_path='ffmpeg'):
    """
    Slow down audio to match a specific tempo (BPM).
    
    Args:
        input_path (str): Path to input audio file
        output_path (str): Path to output audio file  
        new_tempo_bpm (float): Target tempo in beats per minute
        ffmpeg_path (str): Path to ffmpeg executable
    
    Note: This assumes the original audio has a tempo that can be calculated.
    For more precise tempo matching, you'd need additional audio analysis.
    """
    
    print(f"🎼 Tempo-based slowdown to {new_tempo_bpm} BPM")
    print("⚠️  Note: This assumes you know the original tempo")
    
    # This is a simplified version - in practice you'd want to:
    # 1. Detect the original tempo using audio analysis
    # 2. Calculate the exact slowdown factor
    # 3. Apply the slowdown
    
    # For demonstration, assuming common tempos:
    common_tempos = [120, 140, 160, 180]  # Common music tempos
    
    print("🎵 If you know the original tempo, calculate slowdown factor as:")
    for original_tempo in common_tempos:
        factor = original_tempo / new_tempo_bpm
        print(f"   Original {original_tempo} BPM → {new_tempo_bpm} BPM = {factor:.2f}x slowdown")
    
    print("💡 Use slow_down_audio() with the calculated factor")

def batch_slow_down_directory(directory_path, slowdown_factor, output_suffix="_slowed"):
    """
    Slow down all audio files in a directory.
    
    Args:
        directory_path (str): Directory containing audio files
        slowdown_factor (float): Factor to slow down by
        output_suffix (str): Suffix to add to output filenames
    """
    
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        return
    
    directory = Path(directory_path)
    if not directory.exists():
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Common audio extensions
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
    
    audio_files = [
        f for f in directory.iterdir() 
        if f.is_file() and f.suffix.lower() in audio_extensions
        and not f.stem.endswith(output_suffix)  # Skip already processed files
    ]
    
    if not audio_files:
        print(f"❌ No audio files found in {directory_path}")
        return
    
    print(f"📁 Found {len(audio_files)} audio files to process")
    
    successful = 0
    failed = 0
    
    for audio_file in audio_files:
        output_file = audio_file.parent / f"{audio_file.stem}{output_suffix}{audio_file.suffix}"
        
        if output_file.exists():
            print(f"⏭️  Skipping {audio_file.name} (output exists)")
            continue
        
        print(f"\n🎵 Processing: {audio_file.name}")
        
        if slow_down_audio(str(audio_file), str(output_file), slowdown_factor, ffmpeg_path):
            successful += 1
        else:
            failed += 1
    
    print(f"\n📊 Batch processing complete:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")

def main():
    """
    Main function - Configure your audio slowdown here!
    """
    
    print("🎵 High-Quality Audio Slowdown Tool")
    print("=" * 40)
    
    # Check FFmpeg availability
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        print("Please install FFmpeg first!")
        return
    
    # ========================
    # CONFIGURE YOUR SETTINGS HERE
    # ========================
    
    # Single file processing
    input_audio = "test2.wav"          # ← Change this to your input file
    output_audio = "test2s.wav"   # ← Change this to your output file
    slowdown_factor = 1.3             # ← Change this (2.0 = half speed, 1.5 = 2/3 speed)
    
    # Batch processing (uncomment to use)
    # batch_directory = "audio_files"   # ← Directory with audio files
    # batch_slowdown = 1.5              # ← Slowdown factor for batch
    
    # ========================
    # PROCESSING
    # ========================
    
    print(f"\n🎯 Configuration:")
    print(f"   Input: {input_audio}")
    print(f"   Output: {output_audio}")
    print(f"   Slowdown: {slowdown_factor}x")
    
    # Process single file
    if os.path.exists(input_audio):
        print(f"\n🎵 Processing single file...")
        success = slow_down_audio(input_audio, output_audio, slowdown_factor, ffmpeg_path)
        
        if success:
            print(f"\n✅ Success! Slowed audio saved as: {output_audio}")
        else:
            print(f"\n❌ Failed to process audio")
    else:
        print(f"\n⚠️  Input file not found: {input_audio}")
        print("Please update the 'input_audio' variable in main() with your file path")
    
    # Batch processing example (uncomment to use)
    """
    print(f"\n📁 Batch processing example...")
    batch_slow_down_directory(batch_directory, batch_slowdown)
    """
    
    # Tempo example (uncomment to use)
    """
    print(f"\n🎼 Tempo-based example...")
    slow_down_audio_precise_tempo(input_audio, "output_tempo.wav", 80.0, ffmpeg_path)
    """

if __name__ == "__main__":
    main()