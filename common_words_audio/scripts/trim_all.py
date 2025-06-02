import os
import librosa
import soundfile as sf

def trim_trailing_silence_in_folder():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    trimmed_dir = os.path.join(base_dir, "trimmed")
    os.makedirs(trimmed_dir, exist_ok=True)

    for filename in os.listdir(base_dir):
        if filename.endswith(".wav"):
            input_path = os.path.join(base_dir, filename)
            output_path = os.path.join(trimmed_dir, filename)

            audio, sr = librosa.load(input_path, sr=None)   
            original_duration = len(audio) / sr * 1000

            trimmed_audio, _ = librosa.effects.trim(
                audio, 
                top_db=20  # Higher = more aggressive trimming
            )

            trimmed_duration = len(trimmed_audio) / sr * 1000
            sf.write(output_path, trimmed_audio, sr)

            print(f"{filename}: {original_duration:.0f} ms → {trimmed_duration:.0f} ms")

if __name__ == "__main__":
    trim_trailing_silence_in_folder()
