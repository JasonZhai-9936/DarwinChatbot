#!/usr/bin/env python3
"""
Script to build sentences by stitching together individual word audio clips.
"""

import os
import time
from pydub import AudioSegment
from pathlib import Path

# Configuration
PAUSE_BETWEEN_WORDS_MS = 300  # Milliseconds of silence between words
AUDIO_CLIPS_DIR = os.path.join("..", "trimmed") 
OUTPUT_DIR = "sentence_audio"  # Where to save built sentences

# Available words (audio clips we have)
AVAILABLE_WORDS = [
    "the",
    "be",
    "to",
    "of",
    "and",
    "a",
    "in",
    "that",
    "have",
    "it",
    "I",
    "car",
    "drove",
    "saw",
    "an",
    "beagle",
    "with",
    "crash",
    "out",
    "home"
]


def get_audio_clip_path(word):
    """Get the full path to an audio clip for a given word"""
    return os.path.join(AUDIO_CLIPS_DIR, f"{word.lower()}.wav")

def load_word_audio(word):
    """Load audio segment for a specific word"""
    clip_path = get_audio_clip_path(word)
    
    if not os.path.exists(clip_path):
        print(f"⚠ Warning: Audio clip not found for word '{word}' at {clip_path}")
        return None
    
    try:
        audio = AudioSegment.from_wav(clip_path)
        print(f"✓ Loaded audio for: '{word}'")
        return audio
    except Exception as e:
        print(f"✗ Error loading audio for '{word}': {e}")
        return None

def create_silence(duration_ms):
    """Create a silent audio segment of specified duration"""
    return AudioSegment.silent(duration=duration_ms)

def build_sentence_audio(words, output_filename=None, pause_ms=None):
    """
    Build a sentence by stitching together individual word audio clips
    
    Args:
        words (list): List of words to stitch together
        output_filename (str): Optional custom output filename
        pause_ms (int): Optional custom pause duration between words
    
    Returns:
        str: Path to the generated sentence audio file, or None if failed
    """
    if pause_ms is None:
        pause_ms = PAUSE_BETWEEN_WORDS_MS
    
    print(f"\n{'='*50}")
    print(f"Building sentence: {' '.join(words)}")
    print(f"Pause between words: {pause_ms}ms")
    print(f"{'='*50}")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check if all words are available
    missing_words = []
    for word in words:
        if word.lower() not in [w.lower() for w in AVAILABLE_WORDS]:
            missing_words.append(word)
    
    if missing_words:
        print(f"✗ Error: Missing audio clips for words: {missing_words}")
        print(f"Available words: {AVAILABLE_WORDS}")
        return None
    
    # Load audio segments for each word
    audio_segments = []
    silence = create_silence(pause_ms)
    
    for i, word in enumerate(words):
        audio = load_word_audio(word)
        if audio is None:
            print(f"✗ Failed to build sentence - couldn't load '{word}'")
            return None
        
        audio_segments.append(audio)
        
        # Add pause between words (but not after the last word)
        if i < len(words) - 1:
            audio_segments.append(silence)
    
    # Combine all audio segments
    print("🔗 Stitching audio segments together...")
    combined_audio = audio_segments[0]
    for segment in audio_segments[1:]:
        combined_audio += segment
    
    # Generate output filename if not provided
    if output_filename is None:
        sentence_text = "_".join(words).lower()
        timestamp = int(time.time())
        output_filename = f"sentence_{sentence_text}_{timestamp}.wav"
    
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Export the combined audio
    try:
        combined_audio.export(output_path, format="wav")
        print(f"✓ Sentence audio saved to: {output_path}")
        print(f"Duration: {len(combined_audio)/1000:.2f} seconds")
        return output_path
    except Exception as e:
        print(f"✗ Error saving sentence audio: {e}")
        return None

def test_simple_sentences():
    """Test the sentence builder with some simple sentences"""
    
    test_sentences = [
        ["I", "saw", "a", "beagle", "in", "the", "car"],
        ["I", "drove", "home", "with", "the", "beagle"],
        ["crash", "out", "to", "have", "a", "car"],
        ["I", "have", "to", "be", "in", "the", "car"],
        ["the", "car", "crash", "out", "with", "a", "beagle"]
    ]
    
    print("Testing sentence builder with simple sentences...")
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n--- Test {i} ---")
        result = build_sentence_audio(sentence)
        if result:
            print(f"✓ Test {i} successful!")
        else:
            print(f"✗ Test {i} failed!")
        
        # Small delay between tests
        time.sleep(1)

def build_custom_sentence():
    """Interactive function to build a custom sentence"""
    print(f"\nAvailable words: {', '.join(AVAILABLE_WORDS)}")
    print("Enter words separated by spaces (or 'quit' to exit):")
    
    while True:
        user_input = input("\nSentence: ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        if not user_input:
            continue
        
        words = user_input.split()
        result = build_sentence_audio(words)
        
        if result:
            print(f"✓ Sentence built successfully: {result}")
        else:
            print("✗ Failed to build sentence")

def main():
    """Main function"""
    print("Sentence Builder - Stitch together word audio clips")
    print(f"Looking for audio clips in: {os.path.abspath(AUDIO_CLIPS_DIR)}")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
    
    # Check if audio clips directory exists
    if not os.path.exists(AUDIO_CLIPS_DIR):
        print(f"✗ Error: Audio clips directory not found: {AUDIO_CLIPS_DIR}")
        return
    
    # Run tests with simple sentences
    test_simple_sentences()
    
    # Optional: Interactive mode
    print(f"\n{'='*50}")
    print("Would you like to build custom sentences? (y/n)")
    if input().lower().startswith('y'):
        build_custom_sentence()

if __name__ == "__main__":
    main()