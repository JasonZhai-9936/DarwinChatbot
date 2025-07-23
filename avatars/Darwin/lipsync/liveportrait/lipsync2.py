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
    'r': 'r',
    'j': 'y',
    'w': 'w',
}

def count_ipa_vowels(ipa_string):
    """Count vowels in IPA string."""
    return sum(1 for char in ipa_string if char in IPA_VOWELS)

def get_word_ipa_timings(audio_path, model_size="tiny", device="cpu", compute_type="int8"):
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
    return None, None

def check_ffmpeg():
    """Check if ffmpeg is available."""
    ffmpeg_paths = [    
        'ffmpeg',  # In PATH
        'ffmpeg.exe',  # Windows with extension
        r'C:\ffmpeg\ffmpeg\bin\ffmpeg.exe',  # Your specific path
        r'C:\ffmpeg\bin\ffmpeg.exe',  # Common alternative
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',  # Program Files
    ]
    
    for ffmpeg_path in ffmpeg_paths:
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return ffmpeg_path
        except:
            continue
    
    print("❌ FFmpeg not found!")
    return None

def high_quality_speed_adjust(input_path, output_path, target_duration, ffmpeg_path='ffmpeg'):
    """High-quality speed adjustment using our improved method."""
    info = get_video_info(input_path)
    if not info:
        return False
        
    original_duration = info['duration']
    if original_duration <= 0:
        return False
    
    # Calculate speed factor
    speed_factor = original_duration / target_duration
    
    # Build high-quality FFmpeg command
    cmd = [
        ffmpeg_path, '-i', input_path,
        '-filter:v', f'setpts={1/speed_factor}*PTS',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-y', output_path
    ]
    
    # Handle audio if present
    try:
        probe_cmd = [ffmpeg_path, '-i', input_path, '-hide_banner']
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        
        if 'Audio:' in probe_result.stderr:
            if speed_factor > 2:
                atempo_filters = []
                remaining_speed = speed_factor
                while remaining_speed > 2:
                    atempo_filters.append('atempo=2')
                    remaining_speed /= 2
                atempo_filters.append(f'atempo={remaining_speed}')
                
                audio_filter = ','.join(atempo_filters)
                cmd.extend(['-filter:a', audio_filter, '-c:a', 'aac', '-b:a', '320k'])
            else:
                cmd.extend(['-filter:a', f'atempo={speed_factor}', '-c:a', 'aac', '-b:a', '320k'])
            
    except Exception:
        pass
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        return True
    except subprocess.CalledProcessError:
        return False

def create_temp_video(input_videos, durations, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a video by concatenating and timing clips using high-quality speed adjustment."""
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_files = []
        
        for i, (video_path, target_duration) in enumerate(zip(input_videos, durations)):
            if video_path is None:
                continue
                
            info = get_video_info(video_path)
            if not info:
                continue
                
            original_duration = info['duration']
            temp_output = os.path.join(temp_dir, f"segment_{i}.mp4")
            
            # Only adjust speed if the difference is significant (> 0.1 seconds)
            duration_diff = abs(original_duration - target_duration)
            if duration_diff > 0.1:
                if high_quality_speed_adjust(video_path, temp_output, target_duration, ffmpeg_path):
                    temp_files.append(temp_output)
                else:
                    continue
            else:
                # Use original clip duration - no speed adjustment needed for small differences
                cmd = [
                    ffmpeg_path, '-i', video_path,
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                    '-r', str(target_fps),
                    '-y', temp_output
                ]
                
                try:
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
                    temp_files.append(temp_output)
                except subprocess.CalledProcessError:
                    continue
        
        if not temp_files:
            raise RuntimeError("No valid video segments were created")
        
        # Create concat file for ffmpeg
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file}'\n")
        
        # Concatenate all segments with high quality
        concat_cmd = [
            ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, timeout=60)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error concatenating videos: {e}")
            raise

def create_pause_video(duration, silence_video_path, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a pause video by looping a silence clip with high quality."""
    if duration <= 0:
        return None
    
    info = get_video_info(silence_video_path)
    if not info:
        return None
    
    silence_duration = info['duration']
    
    if silence_duration >= duration:
        cmd = [
            ffmpeg_path, '-i', silence_video_path,
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-r', str(target_fps),
            '-y', output_path
        ]
    else:
        loops = int(duration / silence_duration) + 1
        cmd = [
            ffmpeg_path, '-stream_loop', str(loops), '-i', silence_video_path,
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-r', str(target_fps),
            '-y', output_path
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
        return output_path
    except subprocess.CalledProcessError:
        return None

def concatenate_videos_simple(video_files, output_path, ffmpeg_path='ffmpeg'):
    """Concatenate videos with high quality settings."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create concat file for ffmpeg
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for video_file in video_files:
                abs_path = os.path.abspath(video_file)
                f.write(f"file '{abs_path}'\n")
        
        # Concatenate with high quality settings
        concat_cmd = [
            ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, timeout=60)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Error concatenating videos: {e}")
            raise

def print_timing_outline(word_timings):
    """Print a detailed timing outline for words and IPA phonemes."""
    print("\n" + "="*80)
    print("SPEECH TIMING OUTLINE")
    print("="*80)
    
    total_words = len(word_timings)
    total_duration = word_timings[-1]['end'] if word_timings else 0
    
    print(f"📊 SUMMARY: {total_words} words over {total_duration:.2f} seconds")
    print()
    
    for i, word_data in enumerate(word_timings):
        # Parse IPA into phonemes
        phonemes = parse_ipa_string(word_data['ipa'])
        phoneme_duration = word_data['duration'] / len(phonemes) if phonemes else 0
        
        print(f"Word {i+1:2d}: '{word_data['word']}' [{word_data['start']:.2f}s → {word_data['end']:.2f}s] ({word_data['duration']:.2f}s)")
        print(f"         IPA: {word_data['ipa']} → {phonemes}")
        
        # Show individual phoneme timings
        phoneme_start = word_data['start']
        for j, phoneme in enumerate(phonemes):
            phoneme_end = phoneme_start + phoneme_duration
            viseme = IPA_TO_VISEME.get(phoneme, 'MISSING')
            status = "✓" if viseme != 'MISSING' else "✗"
            
            # Indicate if speed adjustment will be applied
            speed_note = ""
            if phoneme_duration < 0.1:
                speed_note = " [no speed adj]"
            
            print(f"           {j+1}. {phoneme:>3} [{phoneme_start:.2f}s → {phoneme_end:.2f}s] → {viseme} {status}{speed_note}")
            phoneme_start = phoneme_end
        print()
    
    print("="*80)

def build_speech_video(word_timings, clips_dir=".", output_path="temp_speech.mp4"):
    """Build the complete speech video from word timing data with high quality."""
    
    print("🎬 Building high-quality speech video...")
    
    # Print timing outline
    print_timing_outline(word_timings)
    
    # Check system
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available!")
    
    # Find a silence clip
    silence_files = ['schwa.mp4', 'a.mp4', 'm.mp4', 'p.mp4']
    silence_video_path = None
    
    for filename in silence_files:
        filepath = Path(clips_dir) / filename
        if filepath.exists():
            info = get_video_info(str(filepath))
            if info and info['duration'] > 0:
                silence_video_path = str(filepath)
                break
    
    if not silence_video_path:
        # Try to find any clip to use as silence
        for file in Path(clips_dir).glob("*.mp4"):
            info = get_video_info(str(file))
            if info and info['duration'] > 0:
                silence_video_path = str(file)
                break
    
    if not silence_video_path:
        raise FileNotFoundError("No valid video clips found in directory!")
    
    print(f"🔇 Using silence clip: {Path(silence_video_path).name}")
    
    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        segment_files = []
        previous_end_time = 0.0
        missing_phonemes = set()
        
        for i, word_data in enumerate(word_timings):
            current_start = word_data['start']
            current_end = word_data['end']
            
            # Handle pause before this word
            pause_duration = current_start - previous_end_time
            if pause_duration > 0.01:
                pause_file = os.path.join(temp_dir, f"pause_{i}.mp4")
                if create_pause_video(pause_duration, silence_video_path, pause_file, ffmpeg_path):
                    segment_files.append(pause_file)
            
            # Parse IPA into individual phonemes
            phonemes = parse_ipa_string(word_data['ipa'])
            
            # Load video clips for each phoneme
            word_videos = []
            word_durations = []
            
            for phoneme in phonemes:
                video_path, info = load_viseme_clip(phoneme, clips_dir)
                if video_path and info:
                    word_videos.append(video_path)
                else:
                    missing_phonemes.add(phoneme)
                    word_videos.append(silence_video_path)
                
                # Distribute duration equally among phonemes
                phoneme_duration = word_data['duration'] / len(phonemes)
                word_durations.append(phoneme_duration)
            
            if word_videos:
                word_file = os.path.join(temp_dir, f"word_{i}.mp4")
                try:
                    create_temp_video(word_videos, word_durations, word_file, ffmpeg_path)
                    segment_files.append(word_file)
                except Exception as e:
                    print(f"❌ Failed to create word video for '{word_data['word']}': {e}")
            
            previous_end_time = current_end
        
        if missing_phonemes:
            print(f"⚠️  Missing viseme clips for: {sorted(missing_phonemes)}")
        
        print(f"📹 Created {len(segment_files)} video segments")
        
        if not segment_files:
            raise RuntimeError("No video segments created")
        
        # Concatenate all segments
        print("🔗 Concatenating video segments...")
        concatenate_videos_simple(segment_files, output_path, ffmpeg_path)
        print(f"✅ Speech video created: {output_path}")
        
        return output_path

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
            cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', audio_path]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            import json
            info = json.loads(result.stdout)
            return info
        except:
            continue
    
    return None

def combine_video_audio(video_path, audio_path, output_path, ffmpeg_path='ffmpeg'):
    """Combine video with audio using ffmpeg with high quality settings."""
    
    print(f"🎵 Combining video and audio...")
    
    # High-quality audio/video combination
    cmd = [
        ffmpeg_path, '-i', video_path, '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-map', '0:v:0', '-map', '1:a:0',
        '-shortest',
        '-y', output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Final video created: {output_path} ({file_size:,} bytes)")
            return output_path
        else:
            raise RuntimeError("Output file creation failed")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to combine audio and video: {e}")
        
        # Try fallback approach
        print(f"🔄 Trying fallback approach...")
        fallback_cmd = [
            ffmpeg_path, '-i', video_path, '-i', audio_path,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
            '-c:a', 'aac', '-b:a', '320k',
            '-map', '0:v:0', '-map', '1:a:0',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(fallback_cmd, check=True, capture_output=True, text=True, timeout=120)
            print(f"✅ Fallback approach successful")
            return output_path
        except subprocess.CalledProcessError:
            raise RuntimeError("All audio combination approaches failed!")

def create_lipsynced_video(audio_path, clips_dir=".", output_path=None):
    """
    Main function: Create a complete lip-synced video from an audio file with high quality.
    
    Args:
        audio_path (str): Path to the input audio file
        clips_dir (str): Directory containing viseme video clips
        output_path (str): Output video file path (auto-generated if None)
    
    Returns:
        str: Path to the created video file
    """
    
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_lipsynced_hq.mp4"
    
    print(f"🎬 Creating HIGH-QUALITY lip-synced video")
    print(f"📁 Audio: {audio_path}")
    print(f"📁 Viseme clips: {clips_dir}")
    print(f"💾 Output: {output_path}")
    
    # Step 1: Analyze audio for word timings
    print("\n🎤 Analyzing audio...")
    word_timings = get_word_ipa_timings(audio_path)
    
    # Step 2: Build video from viseme clips
    print("\n🎬 Building video...")
    temp_video = "temp_speech_video_hq.mp4"
    speech_video_path = build_speech_video(word_timings, clips_dir, temp_video)
    
    # Step 3: Combine with audio
    print("\n🔗 Final assembly...")
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available for audio combining!")
    
    final_output = combine_video_audio(speech_video_path, audio_path, output_path, ffmpeg_path)
    
    # Clean up
    try:
        os.remove(temp_video)
    except:
        pass
    
    print(f"\n🎉 SUCCESS! High-quality lip-synced video created: {final_output}")
    
    return final_output

# Example usage
if __name__ == "__main__":
    create_lipsynced_video("hay.wav", clips_dir="", output_path="hay_lp_12.mp4")