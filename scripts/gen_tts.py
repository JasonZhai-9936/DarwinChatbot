#!/usr/bin/env python3
"""
Standalone script to generate TTS audio clips for the top 10 most common English words
using Groq PlayAI TTS with the same voice settings as the Darwin project.
"""

import os
import time
from groq import Groq
from pathlib import Path

# Load GROQ API key from file one folder up
def load_groq_api_key():
    """Load Groq API key from a file located one folder up from this script"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    api_key_file = os.path.join(parent_dir, "groq_api_key.txt")
    
    with open(api_key_file, 'r', encoding='utf-8') as f:
        api_key = f.read().strip()
        return api_key

def generate_tts_audio(text, output_filename, client):
    """
    Generate TTS audio using Groq PlayAI API with the same settings as Darwin project
    """
    try:
        print(f"Generating TTS for: '{text}'")
        
        # Using the same voice as the Darwin project
        response = client.audio.speech.create(
            model="playai-tts",
            voice="Basil-PlayAI",  # Same voice as Darwin project
            input=text,
            response_format="wav"
        )
        
        # Write the audio data to file
        response.write_to_file(output_filename)
        
        print(f"✓ Successfully generated: {output_filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error generating TTS for '{text}': {e}")
        return False

def main():
    """Generate TTS audio clips for the top 10 most common English words"""
    
    # Top 10 most common English words
    common_words = [
        "drove",
        "saw", 
        "an",
        "beagle",
        "with",
        "to",
        "crash",
        "out",
        "i",
        "home",
        "I",
        "car"
    ]
    
    # Load API key and initialize Groq client
    try:
        api_key = load_groq_api_key()
        client = Groq(api_key=api_key)
        print(f"Groq client initialized successfully")
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return
    
    # Create output directory if it doesn't exist
    output_dir = "common_words_audio"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Generate TTS for each word
    successful = 0
    failed = 0
    
    for word in common_words:
        output_filename = os.path.join(output_dir, f"{word}.wav")
        
        # Skip if file already exists
        if os.path.exists(output_filename):
            print(f"⚠ File already exists, skipping: {output_filename}")
            continue
            
        success = generate_tts_audio(word, output_filename, client)
        
        if success:
            successful += 1
        else:
            failed += 1
            
        # Small delay between requests to be respectful to the API
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*50)
    print(f"TTS Generation Complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print("="*50)

if __name__ == "__main__":
    main()