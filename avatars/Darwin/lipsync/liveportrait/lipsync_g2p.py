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

def get_word_phoneme_timings(audio_path, model_size="tiny", device="cpu", compute_type="int8"):
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

def create_precise_duration_clip(input_path, output_path, target_duration, ffmpeg_path='ffmpeg'):
    """Create a clip with precise target duration using frame-based approach."""
    info = get_video_info(input_path)
    if not info:
        return False
        
    original_duration = info['duration']
    if original_duration <= 0:
        return False
    
    # Calculate target frames at 24fps
    target_frames = max(1, int(target_duration * 24))
    
    if target_duration <= original_duration:
        # Trim to exact frame count
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-vf', f'select=lt(n\\,{target_frames})',
            '-vsync', 'vfr',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
            '-r', '24',
            '-y', output_path
        ]
    else:
        # Loop to reach target frames
        original_frames = int(original_duration * 24)
        loop_count = (target_frames // original_frames) + 1
        
        cmd = [
            ffmpeg_path, '-stream_loop', str(loop_count), '-i', input_path,
            '-vf', f'select=lt(n\\,{target_frames})',
            '-vsync', 'vfr',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
            '-r', '24',
            '-y', output_path
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
        
        # Verify the output
        new_info = get_video_info(output_path)
        if new_info:
            actual_duration = new_info['duration']
            actual_frames = int(actual_duration * 24)
            
            if abs(actual_frames - target_frames) <= 1:  # Within 1 frame tolerance
                print(f"✅ Frame-precise: {original_duration:.3f}s → {actual_duration:.3f}s (target: {target_duration:.3f}s)")
                return True
            else:
                print(f"⚠️ Frame mismatch: got {actual_frames} frames, wanted {target_frames}")
                return True  # Still use it
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Frame-based clip creation failed: {e}")
        
        # Fallback to simple trim/loop
        try:
            if target_duration <= original_duration:
                simple_cmd = [
                    ffmpeg_path, '-i', input_path,
                    '-t', f'{target_duration:.3f}',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                    '-r', '24', '-y', output_path
                ]
            else:
                loops = int(target_duration / original_duration) + 1
                simple_cmd = [
                    ffmpeg_path, '-stream_loop', str(loops), '-i', input_path,
                    '-t', f'{target_duration:.3f}',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                    '-r', '24', '-y', output_path
                ]
            
            subprocess.run(simple_cmd, check=True, capture_output=True, text=True, timeout=30)
            print(f"✅ Simple fallback: {target_duration:.3f}s")
            return True
            
        except subprocess.CalledProcessError:
            return False

def create_temp_video(input_videos, durations, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a video by concatenating clips with precise duration matching using demuxer."""
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_files = []
        
        print(f"🎬 Processing {len(input_videos)} clips for concatenation...")
        
        for i, (video_path, target_duration) in enumerate(zip(input_videos, durations)):
            if video_path is None:
                continue
                
            temp_output = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
            
            # Use precise duration matching
            if create_precise_duration_clip(video_path, temp_output, target_duration, ffmpeg_path):
                # Verify the created clip
                verify_info = get_video_info(temp_output)
                if verify_info and verify_info['duration'] > 0:
                    temp_files.append(temp_output)
                    print(f"   Segment {i+1}: {verify_info['duration']:.3f}s (target: {target_duration:.3f}s)")
                else:
                    print(f"❌ Segment {i+1} verification failed")
            else:
                print(f"❌ Failed to create segment {i+1}")
                continue
        
        if not temp_files:
            raise RuntimeError("No valid video segments were created")
        
        print(f"✅ Successfully created {len(temp_files)} segments")
        
        # Use demuxer concat instead of filter concat for better reliability
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for temp_file in temp_files:
                # Convert to absolute path for safety
                abs_path = os.path.abspath(temp_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        # Use demuxer concatenation for frame-perfect joining
        concat_cmd = [
            ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy',  # Copy streams without re-encoding
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, timeout=60)
            print(f"✅ Concatenation successful")
        except subprocess.CalledProcessError as e:
            print(f"❌ Demuxer concat failed, trying filter concat: {e}")
            
            # Fallback to filter-based concatenation
            filter_inputs = []
            filter_complex = []
            
            for i, temp_file in enumerate(temp_files):
                filter_inputs.extend(['-i', temp_file])
                filter_complex.append(f'[{i}:v]')
            
            filter_str = ''.join(filter_complex) + f'concat=n={len(temp_files)}:v=1:a=0[outv]'
            
            filter_cmd = filter_inputs + [
                '-filter_complex', filter_str,
                '-map', '[outv]',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                '-r', '24',
                '-y', output_path
            ]
            
            full_cmd = [ffmpeg_path] + filter_cmd
            
            try:
                result = subprocess.run(full_cmd, check=True, capture_output=True, text=True, timeout=60)
                print(f"✅ Filter concatenation successful")
            except subprocess.CalledProcessError as e2:
                print(f"❌ Both concat methods failed: {e2}")
                raise

def find_silence_clips(clips_dir="."):
    """Find available silence clips and return them in priority order."""
    # Hard-coded silence clips in priority order
    silence_definitions = [
        'g.mp4',       # Primary - keep as main for calculations
        'p.mp4',       # Secondary - lip closure (good for pauses)
        'eh.mp4'       # Tertiary - neutral mouth position
    ]
    
    available_silences = []
    
    for filename in silence_definitions:
        filepath = Path(clips_dir) / filename
        if filepath.exists():
            info = get_video_info(str(filepath))
            if info and info['duration'] > 0:
                priority = 'primary' if filename == 'g.mp4' else 'secondary' if filename == 'p.mp4' else 'tertiary'
                available_silences.append({
                    'path': str(filepath),
                    'name': filename,
                    'priority': priority,
                    'duration': info['duration']
                })
    
    if not available_silences:
        # Emergency fallback: try to find any clip to use as silence
        for file in Path(clips_dir).glob("*.mp4"):
            info = get_video_info(str(file))
            if info and info['duration'] > 0:
                available_silences.append({
                    'path': str(file),
                    'name': file.name,
                    'priority': 'emergency',
                    'duration': info['duration']
                })
                break
    
    return available_silences

def create_smart_silence_video(duration, available_silences, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a silence video using smart strategies based on duration."""
    if duration <= 0 or not available_silences:
        return None
    
    # Use primary silence clip (g.mp4) for calculations
    primary_silence = available_silences[0]
    primary_duration = primary_silence['duration']
    
    print(f"🔇 Creating {duration:.2f}s silence using {primary_silence['name']} (duration: {primary_duration:.2f}s)")
    
    # Strategy 1: Very short silences (< 1.5x slowdown threshold)
    speed_factor = primary_duration / duration
    if speed_factor > 1.5:
        print(f"   📏 Short silence: Playing normally and cutting at {duration:.2f}s")
        cmd = [
            ffmpeg_path, '-i', primary_silence['path'],
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
    
    # Strategy 2: Medium silences (can slow down within 1.5x limit)
    elif speed_factor <= 1.5 and duration <= primary_duration * 1.5:
        print(f"   🐌 Medium silence: Slowing down by {speed_factor:.1f}x")
        if adjust_clip_speed_to_duration(primary_silence['path'], output_path, duration, ffmpeg_path):
            return output_path
        # Fallback to cutting if speed adjustment fails
        else:
            print(f"   ⚠️  Speed adjustment failed, falling back to cutting")
            cmd = [
                ffmpeg_path, '-i', primary_silence['path'],
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
    
    # Strategy 3: Long silences (slow down clips and loop them)
    else:
        print(f"   🔄 Long silence: Slowing clips by 1.5x and looping")
        
        # Create a temporary slowed-down clip
        with tempfile.TemporaryDirectory() as temp_dir:
            slowed_clip = os.path.join(temp_dir, "slowed_silence.mp4")
            
            # Slow down the primary silence by 1.5x
            slowdown_factor = 1.5
            setpts_multiplier = slowdown_factor  # 1.5 for 1.5x slower
            
            slow_cmd = [
                ffmpeg_path, '-i', primary_silence['path'],
                '-filter:v', f'setpts={setpts_multiplier}*PTS',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                '-y', slowed_clip
            ]
            
            try:
                result = subprocess.run(slow_cmd, check=True, capture_output=True, text=True, timeout=30)
            except subprocess.CalledProcessError:
                # Fallback to original clip if slowing fails
                slowed_clip = primary_silence['path']
            
            # Get duration of slowed clip
            slowed_info = get_video_info(slowed_clip)
            if not slowed_info:
                return None
            
            slowed_duration = slowed_info['duration']
            
            # Use multiple silence clips if available for variety
            loop_clips = [slowed_clip]
            
            # Add other available silence clips (also slowed down)
            for silence in available_silences[1:3]:  # Use up to 2 additional clips
                if silence['priority'] in ['secondary', 'tertiary']:
                    other_slowed = os.path.join(temp_dir, f"slowed_{silence['name']}")
                    slow_other_cmd = [
                        ffmpeg_path, '-i', silence['path'],
                        '-filter:v', f'setpts={setpts_multiplier}*PTS',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                        '-y', other_slowed
                    ]
                    try:
                        result = subprocess.run(slow_other_cmd, check=True, capture_output=True, text=True, timeout=30)
                        loop_clips.append(other_slowed)
                    except subprocess.CalledProcessError:
                        pass  # Skip if this one fails
            
            # Calculate how many loops we need
            total_loop_duration = sum(get_video_info(clip)['duration'] for clip in loop_clips if get_video_info(clip))
            if total_loop_duration <= 0:
                return None
                
            loops_needed = int(duration / total_loop_duration) + 1
            
            print(f"   📼 Using {len(loop_clips)} silence clips, looping {loops_needed} times")
            
            # Create looped sequence
            if len(loop_clips) == 1:
                # Simple case: loop single clip
                cmd = [
                    ffmpeg_path, '-stream_loop', str(loops_needed), '-i', loop_clips[0],
                    '-t', str(duration),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                    '-r', str(target_fps),
                    '-y', output_path
                ]
            else:
                # Complex case: create sequence and loop it
                # First create concat file
                concat_file = os.path.join(temp_dir, "silence_sequence.txt")
                with open(concat_file, 'w') as f:
                    for clip in loop_clips:
                        f.write(f"file '{clip}'\n")
                
                # Create one sequence
                sequence_file = os.path.join(temp_dir, "silence_sequence.mp4")
                seq_cmd = [
                    ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                    '-y', sequence_file
                ]
                
                try:
                    result = subprocess.run(seq_cmd, check=True, capture_output=True, text=True, timeout=30)
                    
                    # Now loop the sequence
                    cmd = [
                        ffmpeg_path, '-stream_loop', str(loops_needed), '-i', sequence_file,
                        '-t', str(duration),
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                        '-r', str(target_fps),
                        '-y', output_path
                    ]
                except subprocess.CalledProcessError:
                    # Fallback to simple looping of first clip
                    cmd = [
                        ffmpeg_path, '-stream_loop', str(loops_needed), '-i', loop_clips[0],
                        '-t', str(duration),
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                        '-r', str(target_fps),
                        '-y', output_path
                    ]
            
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
                return output_path
            except subprocess.CalledProcessError:
                return None

def create_pause_video(duration, silence_video_path, output_path, ffmpeg_path='ffmpeg', target_fps=24):
    """Create a pause video with precise duration."""
    return create_precise_duration_clip(silence_video_path, output_path, duration, ffmpeg_path)

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

def print_final_clip_summary(extended_word_timings, clips_dir="."):
    """Print a clean summary of all clips used with timing and speed information."""
    print("\n" + "="*100)
    print("FINAL CLIP USAGE SUMMARY")
    print("="*100)
    print(f"{'CLIP':<15} {'TIMESTAMP':<20} {'ORIG_LEN':<10} {'NEW_LEN':<10} {'SPEED':<8} {'TYPE':<12} {'WORD/CONTEXT'}")
    print("-" * 100)
    
    clip_counter = 0
    
    for i, word_data in enumerate(extended_word_timings):
        phonemes = word_data['phonemes']
        phoneme_duration = word_data['phoneme_duration']
        extension_duration = word_data['extension_duration']
        remaining_gap = word_data['remaining_gap']
        word_text = word_data['word'].strip()
        
        # Regular phoneme clips
        phoneme_start = word_data['start']
        for j, phoneme in enumerate(phonemes):
            phoneme_end = phoneme_start + phoneme_duration
            viseme_id = get_viseme_from_phoneme(phoneme)
            clip_name = VISEME_TO_IPA_CLIP.get(viseme_id, 'MISSING')
            
            if clip_name and clip_name != 'MISSING':
                clip_path = Path(clips_dir) / f"{clip_name}.mp4"
                if clip_path.exists():
                    clip_info = get_video_info(str(clip_path))
                    if clip_info:
                        original_duration = clip_info['duration']
                        speed_factor = original_duration / phoneme_duration
                        
                        timestamp = f"{phoneme_start:.2f}→{phoneme_end:.2f}s"
                        orig_len = f"{original_duration:.2f}s"
                        new_len = f"{phoneme_duration:.2f}s"
                        speed = f"{speed_factor:.2f}x"
                        clip_type = "phoneme"
                        context = f"{word_text}[{phoneme}]"
                        
                        print(f"{clip_name:<15} {timestamp:<20} {orig_len:<10} {new_len:<10} {speed:<8} {clip_type:<12} {context}")
                        clip_counter += 1
            
            phoneme_start = phoneme_end
        
        # Extension clip (if present)
        if extension_duration > 0.01 and phonemes:
            last_phoneme = phonemes[-1]
            last_viseme_id = get_viseme_from_phoneme(last_phoneme)
            last_clip_name = VISEME_TO_IPA_CLIP.get(last_viseme_id, 'MISSING')
            
            if last_clip_name and last_clip_name != 'MISSING':
                clip_path = Path(clips_dir) / f"{last_clip_name}.mp4"
                if clip_path.exists():
                    clip_info = get_video_info(str(clip_path))
                    if clip_info:
                        original_duration = clip_info['duration']
                        speed_factor = original_duration / extension_duration
                        
                        ext_start = word_data['end']
                        ext_end = ext_start + extension_duration
                        timestamp = f"{ext_start:.2f}→{ext_end:.2f}s"
                        orig_len = f"{original_duration:.2f}s"
                        new_len = f"{extension_duration:.2f}s"
                        speed = f"{speed_factor:.2f}x"
                        clip_type = "extension"
                        context = f"{word_text}[{last_phoneme}] extend"
                        
                        print(f"{last_clip_name:<15} {timestamp:<20} {orig_len:<10} {new_len:<10} {speed:<8} {clip_type:<12} {context}")
                        clip_counter += 1
        
        # Silence clip (if present)
        if remaining_gap > 0.01:
            # Find which silence clip would be used
            silence_files = ['g.mp4', 'p.mp4', 'eh.mp4', 'ae.mp4', 'a.mp4']
            silence_clip_name = None
            silence_original_duration = None
            
            for filename in silence_files:
                filepath = Path(clips_dir) / filename
                if filepath.exists():
                    info = get_video_info(str(filepath))
                    if info and info['duration'] > 0:
                        silence_clip_name = filename.replace('.mp4', '')
                        silence_original_duration = info['duration']
                        break
            
            if silence_clip_name and silence_original_duration:
                speed_factor = silence_original_duration / remaining_gap
                
                silence_start = word_data['extended_end']
                silence_end = silence_start + remaining_gap
                timestamp = f"{silence_start:.2f}→{silence_end:.2f}s"
                orig_len = f"{silence_original_duration:.2f}s"
                new_len = f"{remaining_gap:.2f}s"
                speed = f"{speed_factor:.2f}x"
                clip_type = "silence"
                context = f"gap after '{word_text}'"
                
                print(f"{silence_clip_name:<15} {timestamp:<20} {orig_len:<10} {new_len:<10} {speed:<8} {clip_type:<12} {context}")
                clip_counter += 1
    
    print("-" * 100)
    print(f"TOTAL CLIPS USED: {clip_counter}")
    print("="*100)

def calculate_extended_word_timings(word_timings):
    """Calculate extended word timings by extending words into gaps under 1s."""
    extended_timings = []
    
    for i, word_data in enumerate(word_timings):
        extended_word = word_data.copy()
        
        # Check if there's a next word to calculate gap
        if i < len(word_timings) - 1:
            next_word_start = word_timings[i + 1]['start']
            current_end = word_data['end']
            gap_duration = next_word_start - current_end
            
            # If gap is under 1 second, extend this word to fill the entire gap
            if gap_duration > 0.01 and gap_duration < 1.0:
                extended_word['extended_end'] = next_word_start  # Fill the entire gap
                extended_word['extension_duration'] = gap_duration
                extended_word['remaining_gap'] = 0  # No remaining gap
            else:
                # Gap is >= 1s or too small, don't extend
                extended_word['extended_end'] = current_end
                extended_word['extension_duration'] = 0
                extended_word['remaining_gap'] = gap_duration if gap_duration >= 1.0 else 0
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
    
    # Print final clip summary
    print_final_clip_summary(extended_word_timings, clips_dir)
    
    # Check system
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available!")
    
    # Find primary silence clip
    silence_files = ['g.mp4', 'p.mp4', 'eh.mp4', 'ae.mp4', 'a.mp4']
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
            
            # Debug logging for timing validation
            print(f"🔍 Processing word {i+1}: '{word_data['word'].strip()}' [{current_start:.2f}s → {extended_end:.2f}s]")
            if extension_duration > 0.01:
                print(f"    Extension: {extension_duration:.2f}s")
            if remaining_gap > 0.01:
                print(f"    Remaining gap: {remaining_gap:.2f}s")
            
            # Handle any remaining pause before this word (should be minimal now)
            pause_duration = current_start - previous_extended_end
            if pause_duration > 0.01:
                print(f"🔇 Adding pause before word: {pause_duration:.2f}s")
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
                print(f"🔄 Extending last phoneme '{last_phoneme}' of '{word_data['word']}' for {extension_duration:.2f}s (fills gap)")
            
            if word_videos:
                word_file = os.path.join(temp_dir, f"word_{i}.mp4")
                try:
                    print(f"🎬 Creating word video: {len(word_videos)} clips, total duration: {sum(word_durations):.2f}s")
                    create_temp_video(word_videos, word_durations, word_file, ffmpeg_path)
                    
                    # Verify the created word video
                    word_info = get_video_info(word_file)
                    if word_info:
                        print(f"✅ Word video created: {word_info['duration']:.2f}s actual")
                    
                    segment_files.append(word_file)
                except Exception as e:
                    print(f"❌ Failed to create word video for '{word_data['word']}': {e}")
            
            # Add remaining gap as silence if needed (only for gaps >= 1s)
            if remaining_gap > 0.01:
                print(f"🔇 Adding silence gap: {remaining_gap:.2f}s")
                gap_file = os.path.join(temp_dir, f"gap_{i}.mp4")
                if create_pause_video(remaining_gap, silence_video_path, gap_file, ffmpeg_path):
                    segment_files.append(gap_file)
            
            previous_extended_end = extended_end + remaining_gap
        
        if missing_visemes:
            print(f"⚠️  Missing viseme clips for: {sorted(missing_visemes)}")
        
        print(f"📹 Created {len(segment_files)} video segments")
        
        # Debug: Show all segment files and their durations
        total_duration = 0
        for j, seg_file in enumerate(segment_files):
            seg_info = get_video_info(seg_file)
            if seg_info:
                print(f"   Segment {j+1}: {seg_info['duration']:.2f}s")
                total_duration += seg_info['duration']
        print(f"   Total segments duration: {total_duration:.2f}s")
        
        if not segment_files:
            raise RuntimeError("No video segments created")
        
        # Concatenate all segments
        print("🔗 Concatenating video segments...")
        concatenate_videos_simple(segment_files, output_path, ffmpeg_path)
        
        # Verify final output
        final_info = get_video_info(output_path)
        if final_info:
            print(f"✅ Final video duration: {final_info['duration']:.2f}s")
        
        print(f"✅ Speech video created: {output_path}")
        
        return output_path

def combine_video_audio(video_path, audio_path, output_path, ffmpeg_path='ffmpeg'):
    """Combine video with audio using ffmpeg with high quality settings."""
    
    print(f"🎵 Combining video and audio...")
    
    # Get durations for debugging
    video_info = get_video_info(video_path)
    
    print(f"📹 Video duration: {video_info['duration']:.2f}s" if video_info else "📹 Video duration: unknown")
    
    # Try to get audio duration using ffprobe
    try:
        audio_probe_cmd = [
            ffmpeg_path.replace('ffmpeg', 'ffprobe') if 'ffmpeg' in ffmpeg_path else 'ffprobe',
            '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio_path
        ]
        audio_result = subprocess.run(audio_probe_cmd, capture_output=True, text=True, timeout=10)
        if audio_result.returncode == 0:
            audio_duration = float(audio_result.stdout.strip())
            print(f"🎵 Audio duration: {audio_duration:.2f}s")
        else:
            print(f"🎵 Audio duration: unknown")
    except:
        print(f"🎵 Audio duration: unknown")
    
    # Use audio to determine final duration and ensure smooth playback
    cmd = [
        ffmpeg_path, '-i', audio_path, '-i', video_path,  # Audio first!
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',           # Copy audio without re-encoding
        '-map', '0:a:0',          # Map audio from first input (audio file)
        '-map', '1:v:0',          # Map video from second input (video file)  
        '-video_track_timescale', '24000',  # Force consistent video timescale
        '-y', output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            final_info = get_video_info(output_path)
            final_duration = final_info['duration'] if final_info else 0
            print(f"✅ Final video created: {output_path} ({file_size:,} bytes, {final_duration:.2f}s)")
            return output_path
        else:
            raise RuntimeError("Output file creation failed")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Audio-first approach failed: {e}")
        
        # Try with audio re-encoding fallback
        print(f"🔄 Trying with audio re-encoding...")
        fallback_cmd = [
            ffmpeg_path, '-i', audio_path, '-i', video_path,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
            '-map', '0:a:0', '-map', '1:v:0',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(fallback_cmd, check=True, capture_output=True, text=True, timeout=120)
            print(f"✅ Audio re-encoding successful")
            return output_path
        except subprocess.CalledProcessError as e2:
            print(f"❌ All audio combination methods failed: {e2}")
            
            # Last resort: just copy the video 
            print(f"🔄 Emergency: creating video-only output...")
            emergency_cmd = [
                ffmpeg_path, '-i', video_path,
                '-c:v', 'copy',
                '-an',  # No audio
                '-y', output_path.replace('.mp4', '_video_only.mp4')
            ]
            
            try:
                result = subprocess.run(emergency_cmd, check=True, capture_output=True, text=True, timeout=60)
                print(f"⚠️  Created video-only file. Audio issues detected.")
                return output_path.replace('.mp4', '_video_only.mp4')
            except:
                raise RuntimeError("Complete failure in video creation")

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
    create_phoneme_lipsynced_video("h3.wav", clips_dir="", output_path="hyd_ls_extended22213.mp4")