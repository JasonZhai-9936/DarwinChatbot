import os
import time
from groq import Groq
from pathlib import Path

# Initialize Groq client with API key
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "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"))

# Configuration
SPEECH_OUTPUT_DIR = os.path.join("stream", "speech")
os.makedirs(SPEECH_OUTPUT_DIR, exist_ok=True)

# Available voices for PlayAI TTS
ENGLISH_VOICES = [
    "Fritz-PlayAI", "Sara-PlayAI", "Kyle-PlayAI", "Madison-PlayAI", 
    "Kai-PlayAI", "Ivy-PlayAI", "Ethan-PlayAI", "Grace-PlayAI",
    "Hazel-PlayAI", "Mason-PlayAI", "Zoe-PlayAI", "Oliver-PlayAI",
    "Ruby-PlayAI", "Leo-PlayAI", "Luna-PlayAI", "Finn-PlayAI",
    "Stella-PlayAI", "Theo-PlayAI", "Iris-PlayAI", "Felix-PlayAI",
    "Sage-PlayAI", "Phoenix-PlayAI", "River-PlayAI", "Quinn-PlayAI",
    "Aria-PlayAI", "Hunter-PlayAI"
]

# For a Victorian-era Darwin character, consider these voices:
DARWIN_SUITABLE_VOICES = [
    "Fritz-PlayAI",    # Deep, distinguished
    "Oliver-PlayAI",   # Classic, refined
    "Theo-PlayAI",     # Intellectual tone
    "Felix-PlayAI",    # Sophisticated
    "Mason-PlayAI"     # Authoritative
]

def run_tts(text, voice="Fritz-PlayAI", model="playai-tts", response_format="wav"):
    """
    Generate speech using Groq's PlayAI TTS model
    
    Args:
        text (str): Text to convert to speech (max 10K characters)
        voice (str): Voice to use for generation
        model (str): Model ID ('playai-tts' or 'playai-tts-arabic')
        response_format (str): Audio format ('wav')
    
    Returns:
        str: Path to the generated audio file
    """
    try:
        # Validate input length
        if len(text) > 10000:
            print(f"[TTS] Warning: Text length ({len(text)}) exceeds 10K limit, truncating...")
            text = text[:10000]
        
        # Generate unique filename with timestamp
        timestamp = int(time.time() * 1000)
        filename = f"darwin_speech_{timestamp}.{response_format}"
        speech_file_path = os.path.join(SPEECH_OUTPUT_DIR, filename)
        
        print(f"[TTS] Generating speech with Groq PlayAI...")
        print(f"[TTS] Model: {model}, Voice: {voice}")
        print(f"[TTS] Text length: {len(text)} characters")
        print(f"[TTS] Output file: {speech_file_path}")
        
        # Generate speech using Groq PlayAI TTS
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format
        )
        
        # Write the audio data to file
        response.write_to_file(speech_file_path)
        
        print(f"[TTS] Speech generation completed successfully")
        print(f"[TTS] File saved to: {speech_file_path}")
        
        return speech_file_path
        
    except Exception as e:
        print(f"[TTS] Error generating speech: {e}")
        return None

def run_tts_for_darwin(text):
    """
    Generate speech specifically tuned for Darwin character
    Uses a voice that sounds distinguished and Victorian-era appropriate
    """
    # Choose a voice that suits Darwin's character
    darwin_voice = "Basil-PlayAI"  # Deep, distinguished voice
    return run_tts(text, voice=darwin_voice)

def test_tts():
    """Test function to verify TTS is working"""
    test_text = "Good day! I am Charles Darwin, and I am delighted to share my observations on the natural world with you."
    
    print("[TTS] Testing Groq PlayAI TTS...")
    result = run_tts_for_darwin(test_text)
    
    if result:
        print(f"[TTS] Test successful! Audio file generated: {result}")
        return True
    else:
        print("[TTS] Test failed!")
        return False

if __name__ == "__main__":
    # Test the TTS system
    test_tts()