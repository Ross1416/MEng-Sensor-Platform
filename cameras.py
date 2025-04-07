from picamera2 import Picamera2
from libcamera import controls
import os, cv2
import logging


def setup_cameras():
    """Setup and start both cameras"""
    logging.debug("Setting up cameras")
    camA = Picamera2(0)
    camB = Picamera2(1)

    # Set image size
    config = camA.create_still_configuration({"size": (4608, 2592), "format": "RGB888"})
    camA.align_configuration(config)
    camB.align_configuration(config)
    camA.configure(config)
    camB.configure(config)

    # Setup focus
    camA.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    camB.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    # Start cameras
    camA.start()
    camB.start()

    logging.debug("Setup cameras")
    return (camA, camB)


def capture(cams, pi_type, save_dir=None):
    """Triggers capture on the cameras {cams}. If {save_dir} specified, the images will be saved to {save_dir} as (timestamp)_#.jpg, otherwise the frames will be returned as a tuple."""
    logging.debug("Capturing images")

    frames = []
    for i in range(len(cams)):
        frames.append(cams[i].capture_array("main"))
        if save_dir != None:
            os.makedirs(f"./{save_dir}", exist_ok=True)
            # cv2.imwrite(save_dir + "/" + str(int(time()))+"_" + str(i)+".jpg",frames[i])
            cv2.imwrite(f"{save_dir}/{pi_type}_{i}.jpg", frames[i])

    logging.debug("Captured images")
    return frames
