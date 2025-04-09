def move_assets():
    """
    Moves asset files to their correct locations for both LivePortrait and Spark-TTS.
    This function assumes the assets are in the current/root directory.
    """
    import os
    import shutil
    
    # Define source and destination paths
    darwin_young_src = "darwin_young.png"
    darwin_young_dest = os.path.join("LivePortrait", "assets", "prompts")
    
    davida_mp3_src = "DavidA.mp3"
    davida_mp3_dest = os.path.join("Spark-TTS", "example")
    
    # Create destination directories if they don't exist
    os.makedirs(darwin_young_dest, exist_ok=True)
    os.makedirs(davida_mp3_dest, exist_ok=True)
    
    # Move darwin_young.png to LivePortrait/assets/prompts
    if os.path.exists(darwin_young_src):
        print(f"Moving {darwin_young_src} to {darwin_young_dest}...")
        shutil.copy2(darwin_young_src, os.path.join(darwin_young_dest, os.path.basename(darwin_young_src)))
        print(f"Successfully moved {darwin_young_src}")
    else:
        print(f"Warning: {darwin_young_src} not found in the current directory")
    
    # Move DavidA.mp3 to Spark-TTS/example
    if os.path.exists(davida_mp3_src):
        print(f"Moving {davida_mp3_src} to {davida_mp3_dest}...")
        shutil.copy2(davida_mp3_src, os.path.join(davida_mp3_dest, os.path.basename(davida_mp3_src)))
        print(f"Successfully moved {davida_mp3_src}")
    else:
        print(f"Warning: {davida_mp3_src} not found in the current directory")
    
    print("Asset movement completed")

# Example usage:
# Add this to any of your installer scripts
# After the main installation is complete, call:
# move_assets()