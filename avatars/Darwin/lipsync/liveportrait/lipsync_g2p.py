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

def trim_clip_to_duration(input_path, output_path, target_duration, ffmpeg_path='ffmpeg'):
    """Trim clip to target duration by cutting from the front if needed."""
    info = get_video_info(input_path)
    if not info:
        return False
        
    original_duration = info['duration']
    if original_duration <= 0:
        return False
    
    # If original is shorter than target, use the whole clip
    if original_duration <= target_duration:
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-y', output_path
        ]
    else:
        # Trim from the front: skip the excess seconds at the beginning
        seconds_to_skip = original_duration - target_duration
        cmd = [
            ffmpeg_path, '-ss', str(seconds_to_skip), '-i', input_path,
            '-t', str(target_duration),
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-y', output_path
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        return True
    except subprocess.CalledProcessError:
        return False

def create_temp_video(input_videos, durations, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a video by concatenating and timing clips using trimming instead of speed adjustment."""
    
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
            
            # Always trim to exact duration - no speed adjustment threshold
            if trim_clip_to_duration(video_path, temp_output, target_duration, ffmpeg_path):
                temp_files.append(temp_output)
            else:
                # Fallback: use original clip with basic processing
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
    """Create a pause video by looping a silence clip."""
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

def print_phoneme_timing_outline(word_timings):
    """Print a detailed timing outline for words and phonemes."""
    print("\n" + "="*80)
    print("PHONEME-BASED SPEECH TIMING OUTLINE")
    print("="*80)
    
    total_words = len(word_timings)
    total_duration = word_timings[-1]['end'] if word_timings else 0
    total_phonemes = sum(len(w['phonemes']) for w in word_timings)
    
    print(f"📊 SUMMARY: {total_words} words, {total_phonemes} phonemes over {total_duration:.2f} seconds")
    print()
    
    for i, word_data in enumerate(word_timings):
        phonemes = word_data['phonemes']
        phoneme_duration = word_data['phoneme_duration']
        
        print(f"Word {i+1:2d}: '{word_data['word']}' [{word_data['start']:.2f}s → {word_data['end']:.2f}s] ({word_data['duration']:.2f}s)")
        print(f"         Phonemes: {phonemes}")
        
        # Show individual phoneme timings and visemes
        phoneme_start = word_data['start']
        for j, phoneme in enumerate(phonemes):
            phoneme_end = phoneme_start + phoneme_duration
            viseme_id = get_viseme_from_phoneme(phoneme)
            clip_name = VISEME_TO_IPA_CLIP.get(viseme_id, 'MISSING')
            status = "✓" if clip_name and clip_name != 'MISSING' else "✗"
            
            # Check if we can get clip info for timing note
            trim_note = ""
            if clip_name and clip_name != 'MISSING':
                clip_path = Path('.') / f"{clip_name}.mp4"  # Assuming clips_dir is current dir
                if clip_path.exists():
                    clip_info = get_video_info(str(clip_path))
                    if clip_info:
                        clip_duration = clip_info['duration']
                        if phoneme_duration < clip_duration:
                            trim_note = " [will trim]"
                        elif phoneme_duration > clip_duration:
                            trim_note = " [will loop]"
            
            print(f"           {j+1}. '{phoneme}' [{phoneme_start:.2f}s → {phoneme_end:.2f}s] → viseme:{viseme_id} ({clip_name}) {status}{trim_note}")
            phoneme_start = phoneme_end
        print()
    
    print("="*80)

def build_phoneme_speech_video(word_timings, clips_dir=".", output_path="temp_phoneme_speech.mp4"):
    """Build the complete speech video from phoneme timing data."""
    
    print("🎬 Building phoneme-based speech video...")
    
    # Print timing outline
    print_phoneme_timing_outline(word_timings)
    
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
        previous_end_time = 0.0
        missing_visemes = set()
        
        for i, word_data in enumerate(word_timings):
            current_start = word_data['start']
            current_end = word_data['end']
            
            # Handle pause before this word
            pause_duration = current_start - previous_end_time
            if pause_duration > 0.01:
                pause_file = os.path.join(temp_dir, f"pause_{i}.mp4")
                if create_pause_video(pause_duration, silence_video_path, pause_file, ffmpeg_path):
                    segment_files.append(pause_file)
            
            # Get phonemes for this word
            phonemes = word_data['phonemes']
            
            # Load video clips for each phoneme
            word_videos = []
            word_durations = []
            
            for phoneme in phonemes:
                viseme_id = get_viseme_from_phoneme(phoneme)
                video_path, info = load_viseme_clip(viseme_id, clips_dir)
                
                if video_path and info:
                    word_videos.append(video_path)
                else:
                    clean_phoneme = re.sub(r'[0-9]', '', phoneme.upper())
                    missing_visemes.add(f"phoneme_{clean_phoneme}_viseme_{viseme_id}_{VISEME_TO_IPA_CLIP.get(viseme_id, 'unknown')}")
                    word_videos.append(silence_video_path)
                
                # Use equal duration for each phoneme
                word_durations.append(word_data['phoneme_duration'])
            
            if word_videos:
                word_file = os.path.join(temp_dir, f"word_{i}.mp4")
                try:
                    create_temp_video(word_videos, word_durations, word_file, ffmpeg_path)
                    segment_files.append(word_file)
                except Exception as e:
                    print(f"❌ Failed to create word video for '{word_data['word']}': {e}")
            
            previous_end_time = current_end
        
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
    Main function: Create a complete lip-synced video from an audio file using phoneme-based visemes.
    
    Args:
        audio_path (str): Path to the input audio file
        clips_dir (str): Directory containing viseme video clips
        output_path (str): Output video file path (auto-generated if None)
    
    Returns:
        str: Path to the created video file
    """
    
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_phoneme_lipsynced.mp4"
    
    print(f"🎬 Creating PHONEME-BASED lip-synced video")
    print(f"📁 Audio: {audio_path}")
    print(f"📁 Viseme clips: {clips_dir}")
    print(f"💾 Output: {output_path}")
    
    # Step 1: Analyze audio for word timings and extract phonemes
    print("\n🎤 Analyzing audio and extracting phonemes...")
    word_timings = get_word_phoneme_timings(audio_path)
    
    # Step 2: Build video from phoneme-based viseme clips
    print("\n🎬 Building phoneme-based video...")
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
    
    print(f"\n🎉 SUCCESS! Phoneme-based lip-synced video created: {final_output}")
    
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
    test_phoneme_extraction()
    
    # Create phoneme-based lip-synced video
    create_phoneme_lipsynced_video("hyd.wav", clips_dir="", output_path="hyd_ls_8.mp4")