import eng_to_ipa as ipa
import re
import cv2
import subprocess
import os
import tempfile
from pathlib import Path

# IPA to viseme mapping (same as before)
IPA_TO_VISEME = {
    # Vowels (monophthongs) 22
    'i': 'i',
    'ɪ': 'i_big',
    'e': 'e',
    'ɛ': 'eh',
    'æ': 'ae',
    'a': 'a_plain',
    'ɑ': 'a',
    'ɒ': 'o_short',
    'ɔ': 'aw',
    'o': 'o',
    'ʊ': 'U',
    'u': 'oo',
    'ʉ': 'ux',
    'ɨ': 'ix',
    'ʏ': 'y_short',
    'y': 'y',
    'ø': 'oe',
    'œ': 'oe_open',
    'ə': 'schwa',
    'ɚ': 'er',
    'ɜ': 'er_open',
    'ɝ': 'er_rhotic',
    # Diphthongs  9
    'aɪ': 'eye', 
    'aʊ': 'ow_diph',
    'ɔɪ': 'oy',
    'eɪ': 'ay',
    'oʊ': 'ow',
    'ju': 'yoo',
    'ɪə': 'ear',
    'eə': 'air',
    'ʊə': 'oor',
    # Consonants   27
    'p': 'p',
    'b': 'b',
    't': 't',    
    'd': 'd',
    'k': 'k',
    'g': 'g',
    'ʔ': 'glottal',
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

def get_audio_duration(audio_path, ffmpeg_path='ffmpeg'):
    """Get the duration of an audio file using ffprobe."""
    ffprobe_paths = [
        ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe'),
        ffmpeg_path.replace('ffmpeg', 'ffprobe'),
        'ffprobe.exe',
        'ffprobe'
    ]
    
    for ffprobe_path in ffprobe_paths:
        try:
            cmd = [ffprobe_path, '-v', 'quiet', '-show_entries', 'format=duration', 
                   '-of', 'csv=p=0', audio_path]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            duration = float(result.stdout.strip())
            print(f"✅ Audio duration: {duration:.3f}s")
            return duration
        except:
            continue
    
    print("⚠️ Could not determine audio duration using ffprobe")
    return None

def check_ffmpeg():
    """Check if ffmpeg is available."""
    print("🔍 Checking FFmpeg availability...")
    
    ffmpeg_paths = [    
        'ffmpeg',
        'ffmpeg.exe',
        r'C:\ffmpeg\ffmpeg\bin\ffmpeg.exe',
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    
    for ffmpeg_path in ffmpeg_paths:
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg found: {version_line}")
                return ffmpeg_path
        except:
            continue
    
    print("❌ FFmpeg not found!")
    return None

def parse_ipa_string(ipa_string):
    """Parse IPA string into individual phonemes."""
    # Clean the string
    ipa_clean = re.sub(r"[ˈˌ\s]", "", ipa_string)
    
    # Multi-character IPA symbols (longest first)
    multi_char_symbols = ['tʃ', 'dʒ', 'aɪ', 'aʊ', 'ɔɪ', 'eɪ', 'oʊ', 'ju', 'ɪə', 'eə', 'ʊə']
    
    phonemes = []
    i = 0
    
    while i < len(ipa_clean):
        found = False
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

def text_to_ipa_phonemes(text):
    """Convert text to a list of IPA phonemes."""
    print(f"📝 Converting text to IPA: '{text}'")
    
    # Convert to IPA
    ipa_text = ipa.convert(text)
    print(f"🔤 IPA conversion: {ipa_text}")
    
    # Parse into phonemes
    phonemes = parse_ipa_string(ipa_text)
    print(f"🎵 Phonemes ({len(phonemes)}): {phonemes}")
    
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

def find_viseme_clip(phoneme, clips_dir="."):
    """Find video clip for a phoneme."""
    if phoneme in IPA_TO_VISEME:
        filename = f"{IPA_TO_VISEME[phoneme]}.mp4"
        filepath = Path(clips_dir) / filename
        
        if filepath.exists():
            info = get_video_info(str(filepath))
            if info and info['duration'] > 0:
                return str(filepath)
    
    return None

def find_silence_clip(clips_dir="."):
    """Find a suitable clip to use for silence/missing phonemes."""
    silence_candidates = ['schwa.mp4', 'a.mp4', 'm.mp4', 'p.mp4']
    
    for filename in silence_candidates:
        filepath = Path(clips_dir) / filename
        if filepath.exists():
            info = get_video_info(str(filepath))
            if info and info['duration'] > 0:
                print(f"✅ Using {filename} as silence clip")
                return str(filepath)
    
    # Fallback: use any available clip
    for file in Path(clips_dir).glob("*.mp4"):
        info = get_video_info(str(file))
        if info and info['duration'] > 0:
            print(f"✅ Using fallback silence clip: {file.name}")
            return str(file)
    
    return None

def create_equal_length_video(phonemes, audio_duration, clips_dir=".", output_path="simple_lipsync.mp4", target_fps=24):
    """Create video with phonemes of equal length."""
    
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available!")
    
    if not phonemes:
        raise RuntimeError("No phonemes to process!")
    
    # Calculate duration per phoneme
    duration_per_phoneme = audio_duration / len(phonemes)
    print(f"📊 {len(phonemes)} phonemes, {audio_duration:.3f}s total")
    print(f"📊 Duration per phoneme: {duration_per_phoneme:.3f}s")
    
    # Find silence clip for missing phonemes
    silence_clip = find_silence_clip(clips_dir)
    if not silence_clip:
        raise RuntimeError("No video clips found!")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📂 Using temp directory: {temp_dir}")
        segment_files = []
        
        for i, phoneme in enumerate(phonemes):
            print(f"🎬 Processing phoneme {i+1}/{len(phonemes)}: '{phoneme}'")
            
            # Find video clip for this phoneme
            video_clip = find_viseme_clip(phoneme, clips_dir)
            if not video_clip:
                print(f"   ⚠️ No clip found, using silence")
                video_clip = silence_clip
            else:
                print(f"   ✅ Using clip: {Path(video_clip).name}")
            
            # Create segment with exact duration
            segment_file = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
            
            cmd = [
                ffmpeg_path, '-i', video_clip,
                '-t', str(duration_per_phoneme),  # Exact duration
                '-r', str(target_fps),
                '-y', segment_file
            ]
            
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
                segment_files.append(segment_file)
                print(f"   ✅ Segment created: {duration_per_phoneme:.3f}s")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to create segment: {e}")
                continue
        
        if not segment_files:
            raise RuntimeError("No video segments created!")
        
        print(f"🎬 Concatenating {len(segment_files)} segments...")
        
        # Create concat file
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for segment_file in segment_files:
                f.write(f"file '{segment_file}'\n")
        
        # Concatenate all segments
        concat_cmd = [
            ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy', '-y', output_path
        ]
        
        try:
            result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, timeout=60)
            print(f"✅ Video segments concatenated successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error concatenating segments: {e}")
            raise
    
    return output_path

def combine_video_audio(video_path, audio_path, output_path, ffmpeg_path='ffmpeg'):
    """Combine video with audio."""
    print(f"🎵 Combining video with audio...")
    
    cmd = [
        ffmpeg_path, '-i', video_path, '-i', audio_path,
        '-c:v', 'copy', '-c:a', 'aac',
        '-map', '0:v:0', '-map', '1:a:0',
        '-shortest',  # Use shortest stream duration
        '-y', output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        print(f"✅ Audio combined successfully")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error combining audio: {e}")
        raise

def create_simple_lipsynced_video(text, audio_path, clips_dir=".", output_path=None):
    """
    Create a simple lip-synced video with equal-length phonemes.
    
    Args:
        text (str): The text that was spoken in the audio
        audio_path (str): Path to the audio file
        clips_dir (str): Directory containing viseme clips
        output_path (str): Output path (auto-generated if None)
    
    Returns:
        str: Path to created video
    """
    
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_simple_lipsync.mp4"
    
    print(f"🎬 Creating simple lip-sync video")
    print(f"📝 Text: '{text}'")
    print(f"🎵 Audio: {audio_path}")
    print(f"📁 Clips: {clips_dir}")
    print(f"📤 Output: {output_path}")
    
    # Step 1: Get audio duration
    print(f"\n=== Step 1: Analyzing audio ===")
    ffmpeg_path = check_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not available!")
    
    audio_duration = get_audio_duration(audio_path, ffmpeg_path)
    if not audio_duration:
        raise RuntimeError("Could not determine audio duration!")
    
    # Step 2: Convert text to phonemes
    print(f"\n=== Step 2: Converting text to phonemes ===")
    phonemes = text_to_ipa_phonemes(text)
    
    # Step 3: Create video with equal-length phonemes
    print(f"\n=== Step 3: Creating video ===")
    temp_video = "temp_simple_video.mp4"
    video_path = create_equal_length_video(phonemes, audio_duration, clips_dir, temp_video)
    
    # Step 4: Combine with audio
    print(f"\n=== Step 4: Adding audio ===")
    final_output = combine_video_audio(video_path, audio_path, output_path, ffmpeg_path)
    
    # Clean up
    try:
        os.remove(temp_video)
    except:
        pass
    
    print(f"\n✅ Simple lip-sync video created: {final_output}")
    return final_output

# Example usage
if __name__ == "__main__":
    # Simple usage - just provide text and audio!
    text = "Hello world, this is a test of simple lip sync"
    audio_file = "test2.wav"
    
    # Create the lip-synced video
    create_simple_lipsynced_video(
        text=text,
        audio_path=audio_file,
        clips_dir=".",  # Directory with your .mp4 viseme clips
        output_path="simple_lipsync_output.mp4"
    )