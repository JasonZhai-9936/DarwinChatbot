from faster_whisper import WhisperModel
import nltk
from g2p_en import G2p
import re
import cv2
import numpy as np
import subprocess
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Download required NLTK data
try:
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
except:
    pass

# Phoneme to viseme mapping based on standard lip-sync mappings
PHONEME_TO_VISEME = {
    # Silence/Rest
    'SIL': 0, 'SP': 0, '': 0,
    
    # Vowels
    'AA': 2,   # 'a' in "father" - mouth wide open
    'AE': 1,   # 'a' in "cat" - mouth moderately open
    'AH': 1,   # 'u' in "but" - mouth slightly open
    'AO': 8,   # 'o' in "thought" - mouth rounded
    'AW': 9,   # 'ow' in "house" - diphthong
    'AY': 11,  # 'i' in "price" - diphthong
    'EH': 4,   # 'e' in "pet" - mouth moderately open
    'ER': 5,   # 'er' in "bird" - mouth slightly rounded
    'EY': 11,  # 'a' in "face" - diphthong
    'IH': 6,   # 'i' in "kit" - mouth slightly open
    'IY': 6,   # 'ee' in "fleece" - mouth nearly closed
    'OW': 9,   # 'o' in "goat" - rounded
    'OY': 10,  # 'oy' in "choice" - diphthong
    'UH': 4,   # 'u' in "foot" - mouth moderately rounded
    'UW': 7,   # 'oo' in "goose" - mouth very rounded
    
    # Consonants
    'B': 21,   # 'b' - lips closed
    'CH': 16,  # 'ch' - lips protruded
    'D': 19,   # 'd' - tongue tip to alveolar ridge
    'DH': 17,  # 'th' in "that" - tongue between teeth
    'F': 18,   # 'f' - lower lip to upper teeth
    'G': 20,   # 'g' - back of tongue to soft palate
    'HH': 12,  # 'h' - open mouth, air flow
    'JH': 16,  # 'j' in "judge" - lips protruded
    'K': 20,   # 'k' - back of tongue to soft palate
    'L': 14,   # 'l' - tongue tip up
    'M': 21,   # 'm' - lips closed
    'N': 19,   # 'n' - tongue tip to alveolar ridge
    'NG': 20,  # 'ng' - back of tongue up
    'P': 21,   # 'p' - lips closed
    'R': 13,   # 'r' - tongue tip back
    'S': 15,   # 's' - tongue tip close to alveolar ridge
    'SH': 16,  # 'sh' - lips protruded
    'T': 19,   # 't' - tongue tip to alveolar ridge
    'TH': 17,  # 'th' in "think" - tongue between teeth
    'V': 18,   # 'v' - lower lip to upper teeth
    'W': 7,    # 'w' - lips very rounded
    'Y': 6,    # 'y' - tongue high and forward
    'Z': 15,   # 'z' - tongue tip close to alveolar ridge
    'ZH': 16,  # 'zh' in "measure" - lips protruded
}

# Mapping from viseme ID to IPA clip names
VISEME_TO_IPA_CLIP = {
    0: 'g',  # Silence
    1: 'ae', 2: 'a', 3: 'aw', 4: 'eh', 5: 'er_rhotic', 6: 'i', 7: 'w', 8: 'o',
    9: 'ow_diph', 10: 'oy', 11: 'eye', 12: 'h', 13: 'r', 14: 'l', 15: 's',
    16: 'sh', 17: 'th_voiced', 18: 'f', 19: 't', 20: 'k', 21: 'p'
}

def get_viseme_from_phoneme(phoneme):
    """Get viseme ID from phoneme."""
    # Clean up phoneme (remove stress markers and numbers)
    clean_phoneme = re.sub(r'[0-9]', '', phoneme.upper())
    return PHONEME_TO_VISEME.get(clean_phoneme, 0)

def get_word_phoneme_timings(audio_path, model_size="large-v3", device="cpu", compute_type="int8"):
    """Get word-level phoneme timings from audio file using Whisper + G2P."""
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
    
    # Initialize G2P converter
    g2p = G2p()
    
    results = []

    for segment in segments:
        for word in segment.words:
            word_text = word.word.strip(".,!?\"'").lower()
            
            # Get phonemes using G2P
            try:
                phonemes = g2p(word_text)
                # Filter out empty strings and clean phonemes
                phonemes = [p for p in phonemes if p.strip()]
            except Exception as e:
                print(f"Warning: G2P failed for word '{word_text}': {e}")
                phonemes = []
            
            # If no phonemes found, create a silence phoneme
            if not phonemes:
                phonemes = ['SIL']
            
            num_phonemes = len(phonemes)
            duration = word.end - word.start
            phoneme_duration = duration / num_phonemes if num_phonemes > 0 else 0

            results.append({
                "word": word.word,
                "phonemes": phonemes,
                "start": word.start,
                "end": word.end,
                "duration": duration,
                "num_phonemes": num_phonemes,
                "phoneme_duration": phoneme_duration
            })

    return results

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

def load_viseme_clip(viseme_id, clips_dir="."):
    """Load a video clip for a given viseme ID."""
    if viseme_id in VISEME_TO_IPA_CLIP and VISEME_TO_IPA_CLIP[viseme_id]:
        filename = f"{VISEME_TO_IPA_CLIP[viseme_id]}.mp4"
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

def adjust_clip_speed_to_duration(input_path, output_path, target_duration, ffmpeg_path='ffmpeg'):
    """Adjust clip speed to match target duration by slowing down or speeding up."""
    info = get_video_info(input_path)
    if not info:
        return False
        
    original_duration = info['duration']
    if original_duration <= 0:
        return False
    
    # Calculate speed factor
    # If target > original, we need to slow down (speed < 1.0)
    # If target < original, we need to speed up (speed > 1.0)
    speed_factor = original_duration / target_duration
    
    # Limit extreme speed changes for quality reasons
    min_speed = 0.25  # Don't slow down more than 4x
    max_speed = 4.0   # Don't speed up more than 4x
    
    if speed_factor < min_speed:
        speed_factor = min_speed
        print(f"⚠️  Speed factor limited to {min_speed} (was {original_duration/target_duration:.2f})")
    elif speed_factor > max_speed:
        speed_factor = max_speed
        print(f"⚠️  Speed factor limited to {max_speed} (was {original_duration/target_duration:.2f})")
    
    # Use setpts filter to adjust playback speed
    # setpts multiplier: 1.0 = normal speed, 0.5 = 2x speed, 2.0 = 0.5x speed
    setpts_multiplier = 1.0 / speed_factor
    
    cmd = [
        ffmpeg_path, '-i', input_path,
        '-filter:v', f'setpts={setpts_multiplier}*PTS',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-y', output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        
        # Verify the output duration
        new_info = get_video_info(output_path)
        if new_info:
            actual_duration = new_info['duration']
            print(f"📐 Speed adjusted: {original_duration:.2f}s → {actual_duration:.2f}s (target: {target_duration:.2f}s, factor: {speed_factor:.2f})")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Speed adjustment failed: {e}")
        return False

def create_temp_video(input_videos, durations, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a video by concatenating clips with speed adjustment to match timing."""
    
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
            
            # Always adjust speed to match target duration
            if adjust_clip_speed_to_duration(video_path, temp_output, target_duration, ffmpeg_path):
                temp_files.append(temp_output)
            else:
                # Fallback: use original clip with basic processing
                print(f"⚠️  Using original clip for segment {i} (speed adjustment failed)")
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
                    print(f"❌ Failed to process segment {i}")
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
    """Create a pause video by adjusting speed of silence clip."""
    if duration <= 0:
        return None
    
    # Use speed adjustment instead of looping
    if adjust_clip_speed_to_duration(silence_video_path, output_path, duration, ffmpeg_path):
        return output_path
    
    # Fallback to original method if speed adjustment fails
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

def print_extended_timing_outline(extended_word_timings):
    """Print a detailed timing outline for words and phonemes with extensions."""
    print("\n" + "="*80)
    print("PHONEME-BASED SPEECH TIMING OUTLINE (SPEED ADJUSTMENT + WORD EXTENSION MODE)")
    print("="*80)
    
    total_words = len(extended_word_timings)
    total_duration = extended_word_timings[-1]['extended_end'] + extended_word_timings[-1]['remaining_gap'] if extended_word_timings else 0
    total_phonemes = sum(len(w['phonemes']) for w in extended_word_timings)
    total_extensions = sum(1 for w in extended_word_timings if w['extension_duration'] > 0.01)
    
    print(f"📊 SUMMARY: {total_words} words, {total_phonemes} phonemes over {total_duration:.2f} seconds")
    print(f"🔄 EXTENSIONS: {total_extensions} words will extend their last viseme into gaps")
    print()
    
    for i, word_data in enumerate(extended_word_timings):
        phonemes = word_data['phonemes']
        phoneme_duration = word_data['phoneme_duration']
        extension_duration = word_data['extension_duration']
        remaining_gap = word_data['remaining_gap']
        
        extension_info = ""
        if extension_duration > 0.01:
            extension_info = f" + {extension_duration:.2f}s extension"
        if remaining_gap > 0.01:
            extension_info += f" + {remaining_gap:.2f}s silence"
        
        print(f"Word {i+1:2d}: '{word_data['word']}' [{word_data['start']:.2f}s → {word_data['end']:.2f}s] ({word_data['duration']:.2f}s){extension_info}")
        print(f"         Phonemes: {phonemes}")
        
        # Show individual phoneme timings and visemes
        phoneme_start = word_data['start']
        for j, phoneme in enumerate(phonemes):
            phoneme_end = phoneme_start + phoneme_duration
            viseme_id = get_viseme_from_phoneme(phoneme)
            clip_name = VISEME_TO_IPA_CLIP.get(viseme_id, 'MISSING')
            status = "✓" if clip_name and clip_name != 'MISSING' else "✗"
            
            # Check if we can get clip info for speed adjustment note
            speed_note = ""
            if clip_name and clip_name != 'MISSING':
                clip_path = Path('.') / f"{clip_name}.mp4"  # Assuming clips_dir is current dir
                if clip_path.exists():
                    clip_info = get_video_info(str(clip_path))
                    if clip_info:
                        clip_duration = clip_info['duration']
                        speed_factor = clip_duration / phoneme_duration
                        if speed_factor > 1.1:
                            speed_note = f" [slow to {speed_factor:.1f}x]"
                        elif speed_factor < 0.9:
                            speed_note = f" [speed to {speed_factor:.1f}x]"
                        else:
                            speed_note = " [~same speed]"
            
            print(f"           {j+1}. '{phoneme}' [{phoneme_start:.2f}s → {phoneme_end:.2f}s] → viseme:{viseme_id} ({clip_name}) {status}{speed_note}")
            phoneme_start = phoneme_end
        
        # Show extension if present
        if extension_duration > 0.01:
            last_phoneme = phonemes[-1] if phonemes else 'SIL'
            last_viseme_id = get_viseme_from_phoneme(last_phoneme)
            last_clip_name = VISEME_TO_IPA_CLIP.get(last_viseme_id, 'MISSING')
            extension_end = word_data['end'] + extension_duration
            print(f"           📏 EXTENSION: '{last_phoneme}' [{word_data['end']:.2f}s → {extension_end:.2f}s] → viseme:{last_viseme_id} ({last_clip_name}) [extended]")
        
        # Show remaining silence if present
        if remaining_gap > 0.01:
            silence_start = word_data['extended_end']
            silence_end = silence_start + remaining_gap
            print(f"           🔇 SILENCE: [{silence_start:.2f}s → {silence_end:.2f}s] ({remaining_gap:.2f}s)")
        
        print()
    
    print("="*80)

def calculate_extended_word_timings(word_timings):
    """Calculate extended word timings by extending last viseme into following gaps."""
    extended_timings = []
    
    for i, word_data in enumerate(word_timings):
        extended_word = word_data.copy()
        
        # Check if there's a next word to calculate gap
        if i < len(word_timings) - 1:
            next_word_start = word_timings[i + 1]['start']
            current_end = word_data['end']
            gap_duration = next_word_start - current_end
            
            # If there's a gap > 10ms, extend this word into part of it
            if gap_duration > 0.01:
                # Extend the word to fill up to 75% of the gap (leave some for natural pause)
                max_extension = gap_duration * 0.75
                extended_word['extended_end'] = current_end + max_extension
                extended_word['extension_duration'] = max_extension
                extended_word['remaining_gap'] = gap_duration - max_extension
            else:
                extended_word['extended_end'] = current_end
                extended_word['extension_duration'] = 0
                extended_word['remaining_gap'] = 0
        else:
            # Last word - no extension needed
            extended_word['extended_end'] = word_data['end']
            extended_word['extension_duration'] = 0
            extended_word['remaining_gap'] = 0
        
        extended_timings.append(extended_word)
    
    return extended_timings

def build_phoneme_speech_video(word_timings, clips_dir=".", output_path="temp_phoneme_speech.mp4"):
    """Build the complete speech video from phoneme timing data using speed adjustment and word extension."""
    
    print("🎬 Building phoneme-based speech video with speed adjustment and word extension...")
    
    # Calculate extended word timings
    extended_word_timings = calculate_extended_word_timings(word_timings)
    
    # Print timing outline with extensions
    print_extended_timing_outline(extended_word_timings)
    
    # Check system
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available!")
    
    # Find a silence clip (using g as default silence, then others)
    silence_files = ['g.mp4', 'schwa.mp4', 'ae.mp4', 'a.mp4', 'p.mp4']
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
        previous_extended_end = 0.0
        missing_visemes = set()
        
        for i, word_data in enumerate(extended_word_timings):
            current_start = word_data['start']
            current_end = word_data['end']
            extended_end = word_data['extended_end']
            extension_duration = word_data['extension_duration']
            remaining_gap = word_data['remaining_gap']
            
            # Handle any remaining pause before this word (should be minimal now)
            pause_duration = current_start - previous_extended_end
            if pause_duration > 0.01:
                pause_file = os.path.join(temp_dir, f"pause_{i}.mp4")
                if create_pause_video(pause_duration, silence_video_path, pause_file, ffmpeg_path):
                    segment_files.append(pause_file)
            
            # Get phonemes for this word
            phonemes = word_data['phonemes']
            
            # Load video clips for each phoneme
            word_videos = []
            word_durations = []
            
            # Regular phoneme clips
            for phoneme in phonemes:
                viseme_id = get_viseme_from_phoneme(phoneme)
                video_path, info = load_viseme_clip(viseme_id, clips_dir)
                
                if video_path and info:
                    word_videos.append(video_path)
                else:
                    clean_phoneme = re.sub(r'[0-9]', '', phoneme.upper())
                    missing_visemes.add(f"phoneme_{clean_phoneme}_viseme_{viseme_id}_{VISEME_TO_IPA_CLIP.get(viseme_id, 'unknown')}")
                    word_videos.append(silence_video_path)
                
                # Use equal duration for each phoneme within the word
                word_durations.append(word_data['phoneme_duration'])
            
            # Add extension of the last phoneme if there's extension duration
            if extension_duration > 0.01 and phonemes:
                # Use the last phoneme's viseme for the extension
                last_phoneme = phonemes[-1]
                last_viseme_id = get_viseme_from_phoneme(last_phoneme)
                last_video_path, last_info = load_viseme_clip(last_viseme_id, clips_dir)
                
                if last_video_path and last_info:
                    word_videos.append(last_video_path)
                else:
                    word_videos.append(silence_video_path)
                
                word_durations.append(extension_duration)
                print(f"🔄 Extending last phoneme '{last_phoneme}' of '{word_data['word']}' for {extension_duration:.2f}s")
            
            if word_videos:
                word_file = os.path.join(temp_dir, f"word_{i}.mp4")
                try:
                    create_temp_video(word_videos, word_durations, word_file, ffmpeg_path)
                    segment_files.append(word_file)
                except Exception as e:
                    print(f"❌ Failed to create word video for '{word_data['word']}': {e}")
            
            # Add remaining gap as silence if needed
            if remaining_gap > 0.01:
                gap_file = os.path.join(temp_dir, f"gap_{i}.mp4")
                if create_pause_video(remaining_gap, silence_video_path, gap_file, ffmpeg_path):
                    segment_files.append(gap_file)
            
            previous_extended_end = extended_end + remaining_gap
        
        if missing_visemes:
            print(f"⚠️  Missing viseme clips for: {sorted(missing_visemes)}")
        
        print(f"📹 Created {len(segment_files)} video segments")
        
        if not segment_files:
            raise RuntimeError("No video segments created")
        
        # Concatenate all segments
        print("🔗 Concatenating video segments...")
        concatenate_videos_simple(segment_files, output_path, ffmpeg_path)
        print(f"✅ Speech video created: {output_path}")
        
        return output_path

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
        #'-shortest',
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

def create_phoneme_lipsynced_video(audio_path, clips_dir=".", output_path=None):
    """
    Main function: Create a complete lip-synced video from an audio file using phoneme-based visemes with speed adjustment and word extension.
    
    Args:
        audio_path (str): Path to the input audio file
        clips_dir (str): Directory containing viseme video clips
        output_path (str): Output video file path (auto-generated if None)
    
    Returns:
        str: Path to the created video file
    """
    
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_phoneme_lipsynced_extended.mp4"
    
    print(f"🎬 Creating PHONEME-BASED lip-synced video with SPEED ADJUSTMENT and WORD EXTENSION")
    print(f"📁 Audio: {audio_path}")
    print(f"📁 Viseme clips: {clips_dir}")
    print(f"💾 Output: {output_path}")
    
    # Step 1: Analyze audio for word timings and extract phonemes
    print("\n🎤 Analyzing audio and extracting phonemes...")
    word_timings = get_word_phoneme_timings(audio_path)
    
    # Step 2: Build video from phoneme-based viseme clips with extension
    print("\n🎬 Building phoneme-based video with word extensions...")
    temp_video = "temp_phoneme_speech_video.mp4"
    speech_video_path = build_phoneme_speech_video(word_timings, clips_dir, temp_video)
    
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
    
    print(f"\n🎉 SUCCESS! Phoneme-based lip-synced video with speed adjustment and word extension created: {final_output}")
    
    return final_output

# Test phoneme extraction
def test_phoneme_extraction():
    """Test the phoneme extraction with sample texts."""
    test_texts = [
        "I have $250 in my pocket.",
        "popular pets, e.g. cats and dogs",
        "I refuse to collect the refuse around here.",
        "I'm an activationist.",
        "Hello world, how are you today?"
    ]
    
    g2p = G2p()
    print("\n" + "="*60)
    print("PHONEME EXTRACTION TEST")
    print("="*60)
    
    for text in test_texts:
        words = text.split()
        print(f"\nText: '{text}'")
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word:
                try:
                    phonemes = g2p(clean_word)
                    phonemes = [p for p in phonemes if p.strip()]
                    visemes = [get_viseme_from_phoneme(p) for p in phonemes]
                    clips = [VISEME_TO_IPA_CLIP.get(v, 'MISSING') for v in visemes]
                    
                    print(f"  '{clean_word}' → {phonemes} → visemes: {visemes} → clips: {clips}")
                except Exception as e:
                    print(f"  '{clean_word}' → ERROR: {e}")

# Example usage
if __name__ == "__main__":
    # Test phoneme extraction
    #test_phoneme_extraction()
    
    # Create phoneme-based lip-synced video with speed adjustment and word extension
    create_phoneme_lipsynced_video("ht.wav", clips_dir="", output_path="hyd_ls_extended.mp4")