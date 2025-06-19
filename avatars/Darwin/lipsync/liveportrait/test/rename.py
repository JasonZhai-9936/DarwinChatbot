import os

# Directory containing the videos (change if needed)
directory = "."

# Prefix to remove
prefix = "node_main--"

for filename in os.listdir(directory):
    if filename.endswith(".mp4") and filename.startswith(prefix):
        new_name = filename.replace(prefix, "", 1)
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} -> {new_name}")
