import os
from pathlib import Path
import cv2

# IPA to viseme mapping
IPA_TO_VISEME = {
    # Vowels (monophthongs)
    'i': 'i', 'ɪ': 'i_big', 'e': 'e', 'ɛ': 'eh', 'æ': 'ae', 'a': 'a_plain',
    'ɑ': 'a', 'ɒ': 'o_short', 'ɔ': 'aw', 'o': 'o', 'ʊ': 'U', 'u': 'oo',
    'ʉ': 'ux', 'ɨ': 'ix', 'ʏ': 'y_short', 'y': 'y', 'ø': 'oe', 'œ': 'oe_open',
    'ə': 'schwa', 'ɚ': 'er', 'ɜ': 'er_open', 'ɝ': 'er_rhotic',

    # Diphthongs
    'aɪ': 'eye', 'aʊ': 'ow_diph', 'ɔɪ': 'oy', 'eɪ': 'ay', 'oʊ': 'ow',
    'ju': 'yoo', 'ɪə': 'ear', 'eə': 'air', 'ʊə': 'oor',

    # Consonants
    'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 'k': 'k', 'g': 'g',
    'ʔ': 'glottal', 'm': 'm', 'n': 'n', 'ŋ': 'ng', 'f': 'f', 'v': 'v',
    'θ': 'th_voiceless', 'ð': 'th_voiced', 's': 's', 'z': 'z',
    'ʃ': 'sh', 'ʒ': 'zh', 'h': 'h', 'tʃ': 'ch', 'dʒ': 'j',
    'l': 'l', 'ɹ': 'r', 'j': 'y', 'w': 'w',
}

missing_to_replacement = {
    'a_plain.mp4': 'ae.mp4',
    'h.mp4': 'schwa.mp4',
    'yoo.mp4': 'oo.mp4',
    'ow.mp4': 'aw.mp4',
    'oe.mp4': 'o.mp4',
    'oe_open.mp4': 'aw.mp4',
    'a.mp4': 'a_plain.mp4',
    'er.mp4': 'er_open.mp4',
    'eh.mp4': 'e.mp4',
    'er_rhotic.mp4': 'er_open.mp4',
    'ix.mp4': 'i_big.mp4',
    'y_short.mp4': 'U.mp4',
    'glottal.mp4': 't.mp4'
}

def get_video_duration(filepath):
    cap = cv2.VideoCapture(str(filepath))
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    if fps > 0:
        return round(frame_count / fps, 2)
    return None

def check_missing_clips(clips_dir="."):
    expected_files = {f"{v}.mp4": k for k, v in IPA_TO_VISEME.items()}
    all_files = {f for f in os.listdir(clips_dir) if f.endswith(".mp4")}

    print("\n🎞️ Found clips with durations:")
    for fname in sorted(all_files):
        path = Path(clips_dir) / fname
        duration = get_video_duration(path)
        if duration is not None:
            print(f"{fname:20} — {duration:.2f} sec")
        else:
            print(f"{fname:20} — [unreadable]")

    missing = []
    for fname, ipa in expected_files.items():
        if fname not in all_files:
            missing.append((ipa, fname))

    if missing:
        print(f"\n❌ Missing {len(missing)} IPA video clips:\n")
        for ipa, fname in sorted(missing):
            print(f"IPA '{ipa}' → Missing file: {fname}")
    else:
        print("\n✅ All IPA clips are present!")

if __name__ == "__main__":
    check_missing_clips()
