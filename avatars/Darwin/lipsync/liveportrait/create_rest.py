import os
import shutil
from pathlib import Path

# Your existing mappings
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
    'er_open.mp4': 'er.mp4',      # er_open copied from base er
    'eh.mp4': 'e.mp4',
    'er_rhotic.mp4': 'er.mp4',    # er_rhotic also copied from base er
    'ix.mp4': 'i_big.mp4',
    'y_short.mp4': 'U.mp4',
    'glottal.mp4': 't.mp4',
    'ng.mp4': 'n.mp4',            # ng copied from n (similar nasal sounds)
    'o_short.mp4': 'o.mp4'        # o_short copied from base o
}

def create_replacement_clips(clips_dir="."):
    """
    Creates replacement clips by copying existing clips based on the mapping.
    """
    clips_path = Path(clips_dir)
    
    print("🎬 Creating replacement clips...\n")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for missing_file, source_file in missing_to_replacement.items():
        missing_path = clips_path / missing_file
        source_path = clips_path / source_file
        
        # Check if the missing file already exists
        if missing_path.exists():
            print(f"⏭️  Skipped: {missing_file} (already exists)")
            skipped_count += 1
            continue
        
        # Check if the source file exists
        if not source_path.exists():
            print(f"❌ Error: Source file {source_file} not found for {missing_file}")
            error_count += 1
            continue
        
        try:
            # Copy the source file to create the missing file
            shutil.copy2(source_path, missing_path)
            print(f"✅ Created: {missing_file} ← copied from {source_file}")
            created_count += 1
        except Exception as e:
            print(f"❌ Error copying {source_file} to {missing_file}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} clips")
    print(f"   Skipped: {skipped_count} clips (already existed)")
    print(f"   Errors:  {error_count} clips")
    
    if created_count > 0:
        print(f"\n🎉 Successfully created {created_count} replacement clips!")
    
    return created_count, skipped_count, error_count

def verify_all_clips_present(clips_dir="."):
    """
    Verify that all required IPA clips are now present after creating replacements.
    """
    expected_files = {f"{v}.mp4" for v in IPA_TO_VISEME.values()}
    existing_files = {f for f in os.listdir(clips_dir) if f.endswith(".mp4")}
    
    missing = expected_files - existing_files
    
    print(f"\n🔍 Verification:")
    print(f"   Expected: {len(expected_files)} clips")
    print(f"   Found:    {len(existing_files)} clips")
    
    if missing:
        print(f"   Still missing: {len(missing)} clips")
        print("\n❌ Still missing clips:")
        for fname in sorted(missing):
            print(f"   - {fname}")
        return False
    else:
        print("   ✅ All clips are now present!")
        return True

if __name__ == "__main__":
    # Create replacement clips
    created, skipped, errors = create_replacement_clips()
    
    # Verify all clips are present
    verify_all_clips_present()
    
    if errors > 0:
        print(f"\n⚠️  There were {errors} errors. Please check the source files exist.")