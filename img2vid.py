#!/usr/bin/env python3
#turns img to static video
"""
Static Image to Video Generator
Converts a static image into a high-quality video with configurable duration.
"""

import cv2
import numpy as np
from PIL import Image
import json
import os
import argparse
from pathlib import Path

class ImageToVideoGenerator:
    def __init__(self, config_path="config.json"):
        """Initialize with configuration file."""
        self.config = self.load_config(config_path)
        
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        default_config = {
            "input_image": "input.jpg",
            "output_video": "output.mp4",
            "duration_seconds": 10,
            "fps": 30,
            "video_codec": "mp4v",
            "quality": "high",
            "resolution": {
                "width": 1920,
                "height": 1080
            },
            "maintain_aspect_ratio": True,
            "background_color": [0, 0, 0]  # RGB for letterbox/pillarbox
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
        else:
            # Create default config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file: {config_path}")
            
        return default_config
    
    def load_and_resize_image(self, image_path):
        """Load image and resize to target resolution while maintaining aspect ratio."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Load image with PIL for better format support
        pil_img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
            
        # Convert to numpy array for OpenCV
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        target_width = self.config["resolution"]["width"]
        target_height = self.config["resolution"]["height"]
        
        if self.config["maintain_aspect_ratio"]:
            # Calculate scaling to fit within target resolution
            h, w = img.shape[:2]
            scale = min(target_width / w, target_height / h)
            
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Resize image
            img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Create canvas with background color
            canvas = np.full((target_height, target_width, 3), 
                           self.config["background_color"], dtype=np.uint8)
            
            # Center the image on canvas
            y_offset = (target_height - new_h) // 2
            x_offset = (target_width - new_w) // 2
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = img_resized
            
            return canvas
        else:
            # Stretch to fit exact dimensions
            return cv2.resize(img, (target_width, target_height), 
                            interpolation=cv2.INTER_LANCZOS4)
    
    def get_codec_and_extension(self):
        """Get appropriate codec and file extension based on quality settings."""
        codec_map = {
            "high": ("mp4v", ".mp4"),
            "medium": ("XVID", ".avi"),
            "low": ("MJPG", ".avi")
        }
        
        quality = self.config.get("quality", "high")
        return codec_map.get(quality, codec_map["high"])
    
    def generate_video(self):
        """Generate the video from the static image."""
        print("Loading and processing image...")
        img = self.load_and_resize_image(self.config["input_image"])
        
        # Get video parameters
        fps = self.config["fps"]
        duration = self.config["duration_seconds"]
        total_frames = int(fps * duration)
        
        # Get codec and adjust output filename if needed
        codec, ext = self.get_codec_and_extension()
        output_path = self.config["output_video"]
        if not output_path.endswith(ext):
            output_path = str(Path(output_path).with_suffix(ext))
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(
            output_path, 
            fourcc, 
            fps, 
            (self.config["resolution"]["width"], self.config["resolution"]["height"])
        )
        
        if not out.isOpened():
            raise RuntimeError("Failed to initialize video writer")
        
        print(f"Generating video: {total_frames} frames at {fps} FPS...")
        print(f"Duration: {duration} seconds")
        print(f"Resolution: {self.config['resolution']['width']}x{self.config['resolution']['height']}")
        
        # Write frames
        for frame_num in range(total_frames):
            out.write(img)
            
            # Progress indicator
            if frame_num % (fps * 2) == 0:  # Every 2 seconds
                progress = (frame_num / total_frames) * 100
                print(f"Progress: {progress:.1f}%")
        
        # Release resources
        out.release()
        print(f"Video saved as: {output_path}")
        
        # Display file info
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"File size: {file_size:.2f} MB")

def main():
    parser = argparse.ArgumentParser(description="Generate video from static image")
    parser.add_argument("--config", "-c", default="config.json", 
                       help="Path to configuration file")
    parser.add_argument("--input", "-i", help="Input image path (overrides config)")
    parser.add_argument("--output", "-o", help="Output video path (overrides config)")
    parser.add_argument("--duration", "-d", type=float, 
                       help="Duration in seconds (overrides config)")
    
    args = parser.parse_args()
    
    try:
        generator = ImageToVideoGenerator(args.config)
        
        # Override config with command line arguments
        if args.input:
            generator.config["input_image"] = args.input
        if args.output:
            generator.config["output_video"] = args.output
        if args.duration:
            generator.config["duration_seconds"] = args.duration
            
        generator.generate_video()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())