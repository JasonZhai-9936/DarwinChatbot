from pathlib import Path
IPA_TO_VISEME = {
    # Vowels (monophthongs)
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
clips_dir = Path(".")  # or your actual path
missing = []

for phoneme, filename in IPA_TO_VISEME.items():
    clip_path = clips_dir / f"{filename}.mp4"
    if not clip_path.exists():
        missing.append(f"{filename}.mp4")

if missing:
    print("❌ Missing viseme clips:")
    for f in sorted(set(missing)):
        print(f"  - {f}")
else:
    print("✅ All viseme clips are present.")
