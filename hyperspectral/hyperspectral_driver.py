import os
import numpy as np
import pypylon.pylon as pylon
from time import time
import matplotlib.pyplot as plt


def setup_hyperspectral():
    """Sets up hyperspectral camera and opens connection"""

    cam = pylon.InstantCamera(
        pylon.TlFactory.GetInstance().CreateFirstDevice()
    )
    cam.Open()

    # Get to known state
    cam.UserSetSelector = "Default"
    cam.UserSetLoad.Execute()

    # 2x2 pixel binning
    cam.BinningVertical = 2
    cam.BinningHorizontal = 2

    # Set exposure time and gain
    cam.ExposureTimeAbs.Value = 60000  # (cam.ExposureTimeAbs.Max)
    cam.GainRaw.SetValue(200)  # Set gain to max value

    return cam

def get_nframes(angle):
    return round((angle/27)*800)

def grab_hyperspectral_scene(
    cam, nframes, white_image, dark_image, class_name, calibrate=True
):
    """Grabs {nframes} number of frames from hyperspectral camera"""
    from time import time  # Import the time module

    cam.StartGrabbing(pylon.GrabStrategy_OneByOne)

    scene = np.zeros(
        (cam.Width.Value, nframes, cam.Height.Value), dtype=np.uint8
    )
    i = 0

    print("Grabbing frames")
    while cam.IsGrabbing():

        grab = cam.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)

        if grab.GrabSucceeded():
            scene[:, i, :] = np.transpose(grab.Array)  # uncalibrated
            i += 1

        if i == nframes:
            break
    """
    calibrated_scene = np.zeros_like(scene)

    for frame_idx in range(i):
        calibrated_scene[:, frame_idx, :] = calibrate_hyperspectral(
            scene[:, frame_idx, :],
            np.transpose(white_image),
            np.transpose(dark_image),
        )
    """

    cam.StopGrabbing()

    # print(f"Acquired {nframes} frames in {time()-t0} seconds")

    # Define the directory path to save images to
    base_dir = f"images/{class_name}"
    os.makedirs(base_dir, exist_ok=True)

    # Get next available index to save files to
    num_existing = len([f for f in os.listdir(base_dir) if f.endswith(".npy")])
    index = num_existing // 2 + 1

    # Save the scene and white_image
    scene_path = os.path.join(base_dir, f"{class_name}_{index:03d}.npy")
    white_image_path = os.path.join(base_dir, f"white_image_{index:03d}.npy")

    np.save(scene_path, scene)
    np.save(white_image_path, white_image)

    return scene


def grab_avg_hyperspectral_frames(cam, n_frames):

    cam.StartGrabbing(pylon.GrabStrategy_OneByOne)

    frame_accum = None
    i = 0

    while cam.IsGrabbing():
        grab = cam.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)

        if grab.GrabSucceeded():
            frame = grab.Array

            if frame_accum is None:

                frame_accum = np.zeros_like(frame, dtype=np.float32)

            frame_accum += frame
            i += 1

        if i == n_frames:
            break

    cam.StopGrabbing()

    # Compute the average white image
    avg = frame_accum / n_frames

    return avg


def grab_hyperspectral_frame(cam):
    """Grabs single frames from hyperspectral camera"""

    print("Grabbing frame")
    grab = cam.GrabOne(5000)

    return grab.Array


def get_calibration_array(path):
    """ Gets calibration file at {path} and returns as numpy array""" ""
    return np.loadtxt(path)


def get_wavelength_index(cal_array, wavelength, pixel_binning):
    """Returns closest index of {wavelength} from {cal_array} while accounting for pixel binning"""

    if wavelength < cal_array[0]:
        print("Wavelength out of range: Too small.")
        return 0

    elif wavelength > cal_array[-1]:
        print("Wavelength out of range: Too large.")
        return len(cal_array) // pixel_binning

    for i in range(0, len(cal_array)):
        diff = wavelength - cal_array[i]
        if diff <= 0:
            break

    return int(i / pixel_binning)


def calibrate_hyperspectral(X, W, D):
    """
    Calibrates a hyperspectral image using white and dark reference images.

    - X: Uncalibrated hyperspectral image
    - W: White reference image.
    - D: Dark reference image.

    """
    n = (X.astype(float) - D.astype(float)).clip(0, None)
    d = (W.astype(float) - D.astype(float)).clip(1, None)
    I = (n / d).clip(0, 1) * 255

    return I


def get_white_image(cam):
    """
    Captures the white reference image.

    - cam: Camera object

    """

    # Take 100 frames to average over
    white_image = grab_avg_hyperspectral_frames(cam, n_frames=100)

    return white_image


def get_dark_image(cam, dark_image_path="calibration/dark_image_200_35k.npy"):
    """
    Loads or captures the dark reference image.

    - cam: Camera object.
    - dark_image_path: File path to save/load the dark image.

    """

    if os.path.exists(dark_image_path):
        dark_image = np.load(dark_image_path)
    else:
        print("Capturing new dark image...")
        dark_image = grab_avg_hyperspectral_frames(cam, n_frames=100)
        np.save(dark_image_path, dark_image)
        print(f"Dark image saved as {dark_image_path}")

    return dark_image
