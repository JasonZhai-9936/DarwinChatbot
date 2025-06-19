import eng_to_ipa as ipa
import re
import subprocess
import os
import tempfile
from pathlib import Path

# IPA to viseme mapping
IPA_TO_VISEME = {
    # Vowels
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
    # Diphthongs
    'aɪ': 'eye', 
    'aʊ': 'ow_diph',
    'ɔɪ': 'oy',
    'eɪ': 'ay',
    'oʊ': 'ow',
    'ju': 'yoo',
    'ɪə': 'ear',
    'eə': 'air',
    'ʊə': 'oor',
    # Consonants
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

def check_ffmpeg():
    """Find ffmpeg."""
    ffmpeg_paths = [    
        'ffmpeg',
        'ffmpeg.exe',
        r'C:\ffmpeg\ffmpeg\bin\ffmpeg.exe',
        r'C:\ffmpeg\bin\ffmpeg.exe',
    ]
    
    for ffmpeg_path in ffmpeg_paths:
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Found ffmpeg: {ffmpeg_path}")
                return ffmpeg_path
        except:
            continue
    
    raise RuntimeError("❌ FFmpeg not found!")

def parse_ipa_string(ipa_string):
    """Parse IPA string into phonemes."""
    # Clean it up
    ipa_clean = re.sub(r"[ˈˌ\s]", "", ipa_string)
    
    # Multi-character symbols (check longest first)
    multi_char = ['tʃ', 'dʒ', 'aɪ', 'aʊ', 'ɔɪ', 'eɪ', 'oʊ', 'ju', 'ɪə', 'eə', 'ʊə']
    
    phonemes = []
    i = 0
    
    while i < len(ipa_clean):
        found = False
        for symbol in multi_char:
            if ipa_clean[i:i+len(symbol)] == symbol:
                phonemes.append(symbol)
                i += len(symbol)
                found = True
                break
        
        if not found:
            phonemes.append(ipa_clean[i])
            i += 1
    
    return phonemes

def text_to_phonemes(text):
    """Convert text to phonemes."""
    print(f"📝 Input text: '{text}'")
    
    # Convert to IPA
    ipa_text = ipa.convert(text)
    print(f"🔤 IPA: {ipa_text}")
    
    # Parse into phonemes
    phonemes = parse_ipa_string(ipa_text)
    print(f"🎵 Phonemes: {phonemes}")
    
    return phonemes

def find_clip_files(phonemes, clips_dir="."):
    """Find video files for phonemes."""
    print(f"\n📁 Looking for clips in: {clips_dir}")
    
    # Find fallback clip
    fallback_files = ['schwa.mp4', 'a.mp4', 'm.mp4']
    fallback_clip = None
    
    for filename in fallback_files:
        filepath = Path(clips_dir) / filename
        if filepath.exists():
            fallback_clip = str(filepath)
            print(f"✅ Fallback clip: {filename}")
            break
    
    if not fallback_clip:
        # Use any mp4 file as fallback
        mp4_files = list(Path(clips_dir).glob("*.mp4"))
        if mp4_files:
            fallback_clip = str(mp4_files[0])
            print(f"✅ Using any clip as fallback: {mp4_files[0].name}")
        else:
            raise RuntimeError("❌ No MP4 files found!")
    
    # Map phonemes to actual files
    clip_files = []
    
    for phoneme in phonemes:
        if phoneme in IPA_TO_VISEME:
            filename = f"{IPA_TO_VISEME[phoneme]}.mp4"
            filepath = Path(clips_dir) / filename
            
            if filepath.exists():
                clip_files.append(str(filepath))
                print(f"  {phoneme} -> {filename} ✅")
            else:
                clip_files.append(fallback_clip)
                print(f"  {phoneme} -> {filename} ❌ (using fallback)")
        else:
            clip_files.append(fallback_clip)
            print(f"  {phoneme} -> no mapping ❌ (using fallback)")
    
    return clip_files

def concatenate_clips(clip_files, output_path):
    """Simply concatenate clips with no timing changes."""
    print(f"\n🎬 Concatenating {len(clip_files)} clips...")
    
    ffmpeg_path = check_ffmpeg()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create concat file
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        
        print(f"📝 Writing concat file...")
        with open(concat_file, 'w') as f:
            for i, clip_file in enumerate(clip_files):
                abs_path = os.path.abspath(clip_file)
                f.write(f"file '{abs_path}'\n")
                print(f"  {i+1}. {Path(clip_file).name}")
        
        # Simple concatenation - no speed changes, just join them
        cmd = [
            ffmpeg_path, 
            '-f', 'concat', 
            '-safe', '0', 
            '-i', concat_file,
            '-c', 'copy',  # Copy without re-encoding
            '-y', output_path
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
            print(f"✅ Video created: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e}")
            print(f"   Stderr: {e.stderr}")
            raise

def create_basic_lipsync_video(text, clips_dir=".", output_path="simple.wav"):
    """
    Ultra simple: text -> phonemes -> concatenate clips (no timing changes).
    
    Args:
        text (str): Text to convert
        clips_dir (str): Directory with viseme clips
        output_path (str): Output video file
    
    Returns:
        str: Path to created video
    """
    
    print(f"🎬 Creating basic lip-sync video")
    print(f"📝 Text: '{text}'")
    print(f"📁 Clips dir: {clips_dir}")
    print(f"📤 Output: {output_path}")
    
    # Step 1: Convert text to phonemes
    phonemes = text_to_phonemes(text)
    
    if not phonemes:
        raise RuntimeError("No phonemes generated!")
    
    # Step 2: Find clip files
    clip_files = find_clip_files(phonemes, clips_dir)
    
    # Step 3: Concatenate clips
    result_path = concatenate_clips(clip_files, output_path)
    
    print(f"\n✅ Done! Created: {result_path}")
    print(f"📊 Total clips: {len(clip_files)}")
    print(f"📊 Phonemes: {' '.join(phonemes)}")
    
    return result_path

# Example usage
if __name__ == "__main__":
    # Super simple - just text and done!
    text = "good morning"
    create_basic_lipsync_video(
        text=text,
        clips_dir=".",  # Folder with your .mp4 files
        output_path="basic_output.mp4"
    )