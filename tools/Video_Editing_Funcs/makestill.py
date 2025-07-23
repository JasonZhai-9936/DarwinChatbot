import cv2
import numpy as np
from PIL import Image
import os

# ==================== CONFIG ====================
IMAGE_PATH = "node_main.png"  # Path to your input image
OUTPUT_PATH = "output.mp4"  # Output video file path
DURATION = 10  # Duration in seconds
FPS = 30  # Frames per second
VIDEO_WIDTH = 480  # Output video width (or None to use image width)
VIDEO_HEIGHT = 720  # Output video height (or None to use image height)
# ================================================

def create_still_video():
    """Create a still video from an image"""
    
    # Check if input image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image file '{IMAGE_PATH}' not found!")
        return False
    
    try:
        # Load image using PIL for better format support
        pil_image = Image.open(IMAGE_PATH)
        
        # Convert PIL image to OpenCV format (BGR)
        img_array = np.array(pil_image.convert('RGB'))
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Get original dimensions
        original_height, original_width = img_bgr.shape[:2]
        print(f"Original image size: {original_width}x{original_height}")
        
        # Set output dimensions
        if VIDEO_WIDTH is None or VIDEO_HEIGHT is None:
            output_width = original_width
            output_height = original_height
        else:
            output_width = VIDEO_WIDTH
            output_height = VIDEO_HEIGHT
        
        # Resize image if needed
        if (output_width != original_width) or (output_height != original_height):
            img_bgr = cv2.resize(img_bgr, (output_width, output_height))
            print(f"Resized to: {output_width}x{output_height}")
        
        # Calculate total frames
        total_frames = int(DURATION * FPS)
        print(f"Creating video: {DURATION}s at {FPS}fps = {total_frames} frames")
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(OUTPUT_PATH, fourcc, FPS, (output_width, output_height))
        
        # Write frames
        for frame_num in range(total_frames):
            out.write(img_bgr)
            
            # Progress indicator
            if frame_num % (total_frames // 10) == 0:
                progress = (frame_num / total_frames) * 100
                print(f"Progress: {progress:.1f}%")
        
        # Release everything
        out.release()
        cv2.destroyAllWindows()
        
        print(f"Video created successfully: {OUTPUT_PATH}")
        print(f"Video specs: {output_width}x{output_height}, {DURATION}s, {FPS}fps")
        return True
        
    except Exception as e:
        print(f"Error creating video: {str(e)}")
        return False

if __name__ == "__main__":
    print("Image to Still Video Converter")
    print("=" * 40)
    print(f"Input: {IMAGE_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Duration: {DURATION} seconds")
    print("=" * 40)
    
    success = create_still_video()
    
    if success:
        print("\n✅ Conversion completed successfully!")
    else:
        print("\n❌ Conversion failed!")