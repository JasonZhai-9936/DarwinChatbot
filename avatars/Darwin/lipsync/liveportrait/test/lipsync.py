from faster_whisper import WhisperModel
import eng_to_ipa as ipa
import re
import cv2
import numpy as np
import subprocess
import os
import sys
from pathlib import Path
import tempfile
import shutil

# IPA vowels for counting
IPA_VOWELS = "iɪeɛæɑɒʌɔoʊuʊəɜɚaɨʉɶœøɯɤ"

# Mapping of IPA symbols to video file names
IPA_TO_VISEME = {
    # Vowels (monophthongs) 22
    'i': 'i',
    'ɪ': 'i_big',
    'e': 'e',
    'ɛ': 'eh',    #
    'æ': 'ae',
    'a': 'a_plain',
    'ɑ': 'a',     #
    'ɒ': 'o_short',
    'ɔ': 'aw',
    'o': 'o',
    'ʊ': 'U',
    'u': 'oo',
    'ʉ': 'ux',
    'ɨ': 'ix',    #
    'ʏ': 'y_short',
    'y': 'y',
    'ø': 'oe',
    'œ': 'oe_open',
    'ə': 'schwa',
    'ɚ': 'er',
    'ɜ': 'er_open',    #
    'ɝ': 'er_rhotic',    #
    # Diphthongs  9
    'aɪ': 'eye', 
    'aʊ': 'ow_diph',
    'ɔɪ': 'oy',
    'eɪ': 'ay',
    'oʊ': 'ow',    #   
    'ju': 'yoo',    #
    'ɪə': 'ear',
    'eə': 'air',
    'ʊə': 'oor',
    # Consonants   27
    'p': 'p',
    'b': 'b',
    't': 't',    
    'd': 'd',
    'k': 'k',    #
    'g': 'g',
    'ʔ': 'glottal',    #
    'm': 'm',
    'n': 'n',
    'ŋ': 'ng',
    'f': 'f',
    'v': 'v',
    'θ': 'th_voiceless',
    'ð': 'th_voiced',
    's': 's',
    'z': 'z',
    'ʃ': 'sh',
    'ʒ': 'zh',
    'h': 'h',
    'tʃ': 'ch',
    'dʒ': 'j',
    'l': 'l',
    'ɹ': 'r',
    'j': 'y',
    'w': 'w',
}

def count_ipa_vowels(ipa_string):
    """Count vowels in IPA string."""
    return sum(1 for char in ipa_string if char in IPA_VOWELS)

def get_word_ipa_timings(audio_path, model_size="large-v3", device="cpu", compute_type="int8"):
    """Get word-level IPA timings from audio file."""
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)

    results = []

    for segment in segments:
        for word in segment.words:
            word_text = word.word.strip(".,!?\"'").lower()
            ipa_transcription = ipa.convert(word_text)

            # Clean IPA string and count total symbols and vowels
            ipa_clean = re.sub(r"\s+", "", ipa_transcription)
            ipa_symbols = list(ipa_clean)
            num_ipa_symbols = len(ipa_symbols) if ipa_symbols else 1
            num_vowels = count_ipa_vowels(ipa_clean)

            duration = word.end - word.start
            avg_duration_per_ipa = duration / num_ipa_symbols
            avg_duration_per_vowel = duration / num_vowels if num_vowels else 0

            results.append({
                "word": word.word,
                "ipa": ipa_transcription,
                "start": word.start,
                "end": word.end,
                "duration": duration,
                "num_ipa_symbols": num_ipa_symbols,
                "num_vowels": num_vowels,
                "avg_ipa_duration": avg_duration_per_ipa,
                "avg_vowel_duration": avg_duration_per_vowel
            })

    return results

def parse_ipa_string(ipa_string):
    """Parse IPA string into individual phonemes, handling multi-character symbols."""
    # Clean the string
    ipa_clean = re.sub(r"[ˈˌ\s]", "", ipa_string)  # Remove stress marks and spaces
    
    # List of multi-character IPA symbols (longest first)
    multi_char_symbols = ['tʃ', 'dʒ', 'aɪ', 'aʊ', 'ɔɪ', 'eɪ', 'oʊ', 'ju', 'ɪə', 'eə', 'ʊə']
    
    phonemes = []
    i = 0
    
    while i < len(ipa_clean):
        found = False
        # Check for multi-character symbols first
        for symbol in multi_char_symbols:
            if ipa_clean[i:i+len(symbol)] == symbol:
                phonemes.append(symbol)
                i += len(symbol)
                found = True
                break
        
        if not found:
            phonemes.append(ipa_clean[i])
            i += 1
    
    return phonemes

def get_video_info(video_path):
    """Get video information using OpenCV."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    
    cap.release()
    
    return {
        'fps': fps,
        'frame_count': frame_count,
        'width': width,
        'height': height,
        'duration': duration
    }

def load_viseme_clip(phoneme, clips_dir="."):
    """Load a video clip for a given phoneme."""
    if phoneme in IPA_TO_VISEME:
        filename = f"{IPA_TO_VISEME[phoneme]}.mp4"
        filepath = Path(clips_dir) / filename
        
        if filepath.exists():
            info = get_video_info(str(filepath))
            if info and info['duration'] > 0:
                return str(filepath), info
            else:
                print(f"Warning: Video file corrupted or empty: {filepath}")
                return None, None
        else:
            print(f"Warning: Video file not found: {filepath}")
            return None, None
    else:
        print(f"Warning: No mapping found for phoneme: {phoneme}")
        return None, None

def check_ffmpeg():
    """Check if ffmpeg is available."""
    print("🔍 Checking FFmpeg availability...")
    
    # Check current PATH
    path_env = os.environ.get('PATH', '')
    print(f"PATH environment variable:")
    for p in path_env.split(os.pathsep):
        if 'ffmpeg' in p.lower():
            print(f"  📁 FFmpeg path found: {p}")
    
    # Try different ways to find ffmpeg
    ffmpeg_paths = [    
        'ffmpeg',  # In PATH
        'ffmpeg.exe',  # Windows with extension
        r'C:\ffmpeg\ffmpeg\bin\ffmpeg.exe',  # Your specific path
        r'C:\ffmpeg\bin\ffmpeg.exe',  # Common alternative
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',  # Program Files
    ]
    
    for ffmpeg_path in ffmpeg_paths:
        try:
            print(f"  Trying: {ffmpeg_path}")
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg found at: {ffmpeg_path}")
                print(f"   Version: {version_line}")
                return ffmpeg_path
            else:
                print(f"   ❌ Failed with return code: {result.returncode}")
        except FileNotFoundError:
            print(f"   ❌ Not found at: {ffmpeg_path}")
        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout checking: {ffmpeg_path}")
        except Exception as e:
            print(f"   ❌ Error checking {ffmpeg_path}: {e}")
    
    print("❌ FFmpeg not found in any location!")
    print("💡 Manual check - please run in command prompt:")
    print("   ffmpeg -version")
    print("   C:\\ffmpeg\\ffmpeg\\bin\\ffmpeg.exe -version")
    return None

def create_temp_video(input_videos, durations, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a video by concatenating and timing clips using ffmpeg."""
    
    print(f"    DEBUG: Creating temp video with {len(input_videos)} clips using {ffmpeg_path}")
    for i, (vid, dur) in enumerate(zip(input_videos, durations)):
        print(f"      Clip {i}: {vid} -> {dur:.3f}s")
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"    DEBUG: Using temp dir: {temp_dir}")
        temp_files = []
        
        for i, (video_path, target_duration) in enumerate(zip(input_videos, durations)):
            if video_path is None:
                print(f"    DEBUG: Skipping None video at index {i}")
                continue
                
            # Get original video info
            info = get_video_info(video_path)
            if not info:
                print(f"    DEBUG: Could not get info for {video_path}")
                continue
                
            original_duration = info['duration']
            speed_factor = original_duration / target_duration
            
            temp_output = os.path.join(temp_dir, f"segment_{i}.mp4")
            
            # Build ffmpeg command for speed adjustment
            if abs(speed_factor - 1.0) > 0.01:  # Significant speed change needed
                cmd = [
                    ffmpeg_path, '-i', video_path,
                    '-filter:v', f'setpts={speed_factor}*PTS',
                    '-r', str(target_fps),
                    '-y', temp_output
                ]
            else:
                # Just copy without speed change
                cmd = [
                    ffmpeg_path, '-i', video_path,
                    '-r', str(target_fps),
                    '-y', temp_output
                ]
            
            print(f"    DEBUG: Running command: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
                temp_files.append(temp_output)
                print(f"  ✅ Processed segment {i}: {original_duration:.3f}s -> {target_duration:.3f}s (speed: {speed_factor:.3f}x)")
            except subprocess.TimeoutExpired:
                print(f"  ❌ Timeout processing segment {i}")
                continue
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed to process segment {i}")
                print(f"    Command: {' '.join(cmd)}")
                print(f"    Error code: {e.returncode}")
                print(f"    Stderr: {e.stderr}")
                print(f"    Stdout: {e.stdout}")
                continue
            except Exception as e:
                print(f"  ❌ Unexpected error processing segment {i}: {e}")
                continue
        
        if not temp_files:
            print("    DEBUG: No temp files created!")
            raise RuntimeError("No valid video segments were created")
        
        print(f"    DEBUG: Created {len(temp_files)} temp files")
        
        # Create concat file for ffmpeg
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file}'\n")
        
        print(f"    DEBUG: Concat file content:")
        with open(concat_file, 'r') as f:
            print(f"      {f.read()}")
        
        # Concatenate all segments
        concat_cmd = [
            ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy', '-y', output_path
        ]
        
        print(f"    DEBUG: Final concat command: {' '.join(concat_cmd)}")
        
        try:
            result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, timeout=60)
            print(f"  ✅ Successfully created concatenated video: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error concatenating videos:")
            print(f"    Command: {' '.join(concat_cmd)}")
            print(f"    Error code: {e.returncode}")
            print(f"    Stderr: {e.stderr}")
            print(f"    Stdout: {e.stdout}")
            raise

def create_pause_video(duration, silence_video_path, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a pause video by looping a silence clip."""
    if duration <= 0:
        print(f"    DEBUG: Invalid pause duration: {duration}")
        return None
    
    print(f"    DEBUG: Creating pause video - duration: {duration:.3f}s, silence: {silence_video_path}")
    
    # Get info about silence video
    info = get_video_info(silence_video_path)
    if not info:
        print(f"    DEBUG: Could not get info for silence video: {silence_video_path}")
        return None
    
    silence_duration = info['duration']
    print(f"    DEBUG: Silence video duration: {silence_duration:.3f}s")
    
    if silence_duration >= duration:
        # Just trim the silence video
        cmd = [
            ffmpeg_path, '-i', silence_video_path,
            '-t', str(duration),
            '-r', str(target_fps),
            '-y', output_path
        ]
    else:
        # Loop the silence video
        loops = int(duration / silence_duration) + 1
        print(f"    DEBUG: Need to loop {loops} times")
        cmd = [
            ffmpeg_path, '-stream_loop', str(loops), '-i', silence_video_path,
            '-t', str(duration),
            '-r', str(target_fps),
            '-y', output_path
        ]
    
    print(f"    DEBUG: Pause command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
        print(f"    ✅ Pause video created successfully")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Error creating pause video:")
        print(f"      Command: {' '.join(cmd)}")
        print(f"      Error code: {e.returncode}")
        print(f"      Stderr: {e.stderr}")
        print(f"      Stdout: {e.stdout}")
        return None
    except Exception as e:
        print(f"    ❌ Unexpected error creating pause video: {e}")
        return None

def debug_system():
    """Debug system setup and files."""
    print("=== SYSTEM DEBUG ===")
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # List all MP4 files
    mp4_files = list(current_dir.glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 files:")
    for f in mp4_files:
        info = get_video_info(str(f))
        status = f"✅ OK ({info['duration']:.3f}s)" if info else "❌ BAD"
        print(f"  {f.name}: {status}")
    
    # Check Python environment
    print(f"Python executable: {sys.executable}")
    
    return mp4_files

def concatenate_videos_simple(video_files, output_path, ffmpeg_path='ffmpeg'):
    """Concatenate videos without any speed changes using ffmpeg concat demuxer."""
    print(f"📹 Concatenating {len(video_files)} videos without speed changes...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create concat file for ffmpeg
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for video_file in video_files:
                # Use absolute paths to avoid issues
                abs_path = os.path.abspath(video_file)
                f.write(f"file '{abs_path}'\n")
        
        print(f"📝 Concat file content:")
        with open(concat_file, 'r') as f:
            print(f"    {f.read()}")
        
        # Concatenate without any speed changes - just join them
        concat_cmd = [
            ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy', '-y', output_path
        ]
        
        print(f"🔧 Final concat command: {' '.join(concat_cmd)}")
        
        try:
            result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, timeout=60)
            print(f"✅ Successfully concatenated videos: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Error concatenating videos:")
            print(f"    Command: {' '.join(concat_cmd)}")
            print(f"    Error code: {e.returncode}")
            print(f"    Stderr: {e.stderr}")
            print(f"    Stdout: {e.stdout}")
            raise

def build_speech_video(word_timings, clips_dir=".", output_path="temp_speech.mp4"):
    """Build the complete speech video from word timing data."""
    
    print("\n=== DEBUGGING BUILD_SPEECH_VIDEO ===")
    
    # Debug system first
    ffmpeg_path = check_ffmpeg()
    available_files = debug_system()
    
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available!")
    
    # Find a silence clip (try common neutral positions)
    silence_files = ['schwa.mp4', 'a.mp4', 'm.mp4', 'p.mp4']
    silence_video_path = None
    
    print(f"\nLooking for silence clips...")
    for filename in silence_files:
        filepath = Path(clips_dir) / filename
        print(f"  Checking {filepath}: {'EXISTS' if filepath.exists() else 'NOT FOUND'}")
        if filepath.exists():
            info = get_video_info(str(filepath))
            if info and info['duration'] > 0:
                silence_video_path = str(filepath)
                print(f"✅ Using {filename} as silence clip (duration: {info['duration']:.3f}s)")
                break
            else:
                print(f"  {filename} exists but is corrupted")
    
    if not silence_video_path:
        print("Warning: No silence clip found. Using first available clip.")
        # Try to find any clip to use as silence
        for file in Path(clips_dir).glob("*.mp4"):
            info = get_video_info(str(file))
            if info and info['duration'] > 0:
                silence_video_path = str(file)
                print(f"✅ Using fallback silence clip: {file.name}")
                break
    
    if not silence_video_path:
        raise FileNotFoundError("No valid video clips found in directory!")
    
    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\nUsing temporary directory: {temp_dir}")
        segment_files = []
        previous_end_time = 0.0
        
        for i, word_data in enumerate(word_timings):
            print(f"\n--- PROCESSING WORD {i} ---")
            current_start = word_data['start']
            current_end = word_data['end']
            
            # Handle pause before this word
            pause_duration = current_start - previous_end_time
            if pause_duration > 0.01:  # Only add pause if > 10ms
                print(f"Creating pause: {pause_duration:.3f}s")
                pause_file = os.path.join(temp_dir, f"pause_{i}.mp4")
                try:
                    if create_pause_video(pause_duration, silence_video_path, pause_file, ffmpeg_path):
                        segment_files.append(pause_file)
                        print(f"✅ Pause created: {pause_file}")
                    else:
                        print(f"❌ Failed to create pause")
                except Exception as e:
                    print(f"❌ Exception creating pause: {e}")
            
            # Create video for current word
            print(f"Processing word: '{word_data['word']}' -> {word_data['ipa']} (duration: {word_data['duration']:.3f}s)")
            
            # Parse IPA into individual phonemes
            phonemes = parse_ipa_string(word_data['ipa'])
            print(f"  Phonemes: {phonemes}")
            
            # Load video clips for each phoneme
            word_videos = []
            word_durations = []
            
            for j, phoneme in enumerate(phonemes):
                print(f"    Phoneme {j}: '{phoneme}'")
                video_path, info = load_viseme_clip(phoneme, clips_dir)
                if video_path and info:
                    word_videos.append(video_path)
                    # Distribute duration equally among phonemes
                    phoneme_duration = word_data['duration'] / len(phonemes)
                    word_durations.append(phoneme_duration)
                    print(f"      ✅ Found: {video_path} (duration: {phoneme_duration:.3f}s)")
                else:
                    # Use silence clip for missing phonemes
                    word_videos.append(silence_video_path)
                    phoneme_duration = word_data['duration'] / len(phonemes)
                    word_durations.append(phoneme_duration)
                    print(f"      ⚠️  Using silence for missing phoneme: {phoneme}")
            
            if word_videos:
                word_file = os.path.join(temp_dir, f"word_{i}.mp4")
                print(f"  Creating word video: {word_file}")
                try:
                    create_temp_video(word_videos, word_durations, word_file, ffmpeg_path)
                    segment_files.append(word_file)
                    print(f"✅ Word video created: {word_file}")
                except Exception as e:
                    print(f"❌ Failed to create word video: {e}")
                    import traceback
                    traceback.print_exc()
            
            previous_end_time = current_end
        
        print(f"\n=== FINAL CONCATENATION (FIXED) ===")
        print(f"Created {len(segment_files)} segments:")
        for f in segment_files:
            print(f"  {f}")
        
        if not segment_files:
            raise RuntimeError("Error: No video segments created")
        
        # FIXED: Concatenate all segments without any speed changes
        print("Concatenating all video segments without speed modifications...")
        try:
            concatenate_videos_simple(segment_files, output_path, ffmpeg_path)
            print(f"✅ Final video created: {output_path}")
        except Exception as e:
            print(f"❌ Failed to create final video: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        return output_path

def get_audio_info(audio_path, ffmpeg_path='ffmpeg'):
    """Get audio file information using ffprobe."""
    # Try to find ffprobe
    ffprobe_paths = [
        ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe'),
        ffmpeg_path.replace('ffmpeg', 'ffprobe'),
        'ffprobe.exe',
        'ffprobe'
    ]
    
    for ffprobe_path in ffprobe_paths:
        try:
            cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', audio_path]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            import json
            info = json.loads(result.stdout)
            return info
        except:
            continue
    
    print(f"⚠️  Could not find ffprobe to verify audio (but this is not critical)")
    return None

def combine_video_audio(video_path, audio_path, output_path, ffmpeg_path='ffmpeg'):
    """Combine video with audio using ffmpeg."""
    
    print(f"📊 Analyzing audio file: {audio_path}")
    audio_info = get_audio_info(audio_path, ffmpeg_path)
    if audio_info:
        print(f"  Audio format: {audio_info.get('format', {}).get('format_name', 'unknown')}")
        for stream in audio_info.get('streams', []):
            if stream.get('codec_type') == 'audio':
                print(f"  Audio codec: {stream.get('codec_name', 'unknown')}")
                print(f"  Sample rate: {stream.get('sample_rate', 'unknown')}")
                print(f"  Channels: {stream.get('channels', 'unknown')}")
                break
    
    print(f"📊 Analyzing video file: {video_path}")
    video_info = get_video_info(video_path)
    if video_info:
        print(f"  Video duration: {video_info['duration']:.3f}s")
        print(f"  Video FPS: {video_info['fps']}")
    
    # Try multiple approaches for combining audio and video
    approaches = [
        {
            'name': 'Standard copy with AAC',
            'cmd': [
                ffmpeg_path, '-i', video_path, '-i', audio_path,
                '-c:v', 'copy', '-c:a', 'aac',
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest',
                '-y', output_path
            ]
        },
        {
            'name': 'Force re-encode audio',
            'cmd': [
                ffmpeg_path, '-i', video_path, '-i', audio_path,
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                '-map', '0:v:0', '-map', '1:a:0',
                '-y', output_path
            ]
        },
        {
            'name': 'Simple replace audio',
            'cmd': [
                ffmpeg_path, '-i', video_path, '-i', audio_path,
                '-c:v', 'copy', '-c:a', 'copy',
                '-map', '0:v:0', '-map', '1:a:0',
                '-y', output_path
            ]
        }
    ]
    
    for i, approach in enumerate(approaches):
        print(f"\n🎵 Trying approach {i+1}: {approach['name']}")
        cmd = approach['cmd']
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
            print(f"✅ Success with approach: {approach['name']}")
            
            # Check if output file exists and has reasonable size
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ Output file created: {output_path} ({file_size} bytes)")
                
                # Try to verify audio (optional)
                output_info = get_audio_info(output_path, ffmpeg_path)
                if output_info:
                    has_audio = any(stream.get('codec_type') == 'audio' for stream in output_info.get('streams', []))
                    if has_audio:
                        print(f"✅ Output file confirmed to have audio")
                    else:
                        print(f"⚠️  Output file may not have audio, but continuing...")
                else:
                    print(f"⚠️  Could not verify audio (ffprobe not available), but file created successfully")
                
                return output_path
            else:
                print(f"❌ Output file was not created")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed with approach: {approach['name']}")
            print(f"    Error code: {e.returncode}")
            print(f"    Stderr: {e.stderr}")
            if i < len(approaches) - 1:
                print(f"    Trying next approach...")
            continue
        except Exception as e:
            print(f"❌ Unexpected error with approach: {approach['name']}: {e}")
            continue
    
    raise RuntimeError("All audio combination approaches failed!")

def create_lipsynced_video(audio_path, clips_dir=".", output_path=None):
    """
    Main function: Create a complete lip-synced video from an audio file.
    
    Args:
        audio_path (str): Path to the input audio file
        clips_dir (str): Directory containing viseme video clips
        output_path (str): Output video file path (auto-generated if None)
    
    Returns:
        str: Path to the created video file
    """
    
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_lipsynced.mp4"
    
    print(f"Creating lip-synced video from: {audio_path}")
    print(f"Using viseme clips from: {clips_dir}")
    print(f"Output will be saved as: {output_path}")
    
    # Step 1: Analyze audio for word timings
    print("\n=== Step 1: Analyzing audio ===")
    word_timings = get_word_ipa_timings(audio_path)
    
    # Print analysis results
    print("\nWord timing analysis:")
    for item in word_timings:
        print(f"[{item['start']:.2f}s -> {item['end']:.2f}s] {item['word']} -> {item['ipa']} | "
              f"{item['num_ipa_symbols']} IPA symbols, {item['num_vowels']} vowels | "
              f"Avg IPA dur: {item['avg_ipa_duration']:.3f}s, Avg vowel dur: {item['avg_vowel_duration']:.3f}s")
    
    # Step 2: Build video from viseme clips
    print("\n=== Step 2: Building video ===")
    temp_video = "temp_speech_video.mp4"
    speech_video_path = build_speech_video(word_timings, clips_dir, temp_video)
    
    # Step 3: Combine with audio
    print("\n=== Step 3: Combining with audio ===")
    
    # Get ffmpeg path again for audio combining
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available for audio combining!")
    
    final_output = combine_video_audio(speech_video_path, audio_path, output_path, ffmpeg_path)
    
    # Clean up temporary file
    try:
        os.remove(temp_video)
    except:
        pass
    
    print(f"\n✅ Lip-synced video created successfully: {final_output}")
    return final_output

# Example usage
if __name__ == "__main__":
    # Simple one-line usage - just provide your audio file!
    create_lipsynced_video("test2.wav", clips_dir="", output_path="speech1_lipsynced.mp4")