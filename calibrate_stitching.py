import os
import subprocess
from datetime import datetime

def capture_image(camera_id, save_dir):
    """Captures an image using libcamera-still for a specific camera ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"camera_{camera_id}_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)
    
    command = [
        "libcamera-still", 
        "-t", "1000",  # Capture timeout
        "--camera", str(camera_id),  # Select camera
        "-o", filepath  # Output file path
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Image captured: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image from camera {camera_id}: {e}")

def main():
    save_dir = "./calibrate_stitching_image"  # Change this to your desired directory
    os.makedirs(save_dir, exist_ok=True)
    
    # Capture from both cameras (0 and 1 assumed)
    capture_image(0, save_dir)
    capture_image(1, save_dir)

if __name__ == "__main__":
    main()
