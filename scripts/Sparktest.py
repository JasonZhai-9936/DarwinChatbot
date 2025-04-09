from SparkTTS import run_tts

# Generate TTS audio and get the path to the output file
output_file = run_tts(
    text="Hello, my name is Charles Darwin",
    device="0"  # Optional, defaults to "0"
)

if output_file:
    print(f"TTS generated successfully: {output_file}")
else:
    print("TTS generation failed")