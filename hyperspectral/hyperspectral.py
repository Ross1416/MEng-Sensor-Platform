from zaber_driver import *
from hyperspectral.hyperspectral_driver import *
import matplotlib.pyplot as plt
import os


def take_hyperspectral_image(PORT, nframe, angle, calibration):

    try:
        # Get Calibration
        cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)
        # print(get_wavelength_index(calibration_array,450,1))

        # Setup hyperspectral
        cam = setup_hyperspectral(exposure_time, cam_gain, pixel_binning)
        fps = cam.ResultingFrameRateAbs.Value

        print("Setup Hyperspectral Camera")

        # Get white and dark image for lighting calibration
        dark_image = get_dark_image(cam)
        white_image = get_white_image(cam)

        # Show white img
        plt.figure()
        plt.imshow(white_image)
        plt.show()

        # Show dark img
        plt.figure()
        plt.imshow(dark_image)
        plt.show()

        # Get required rotation speed
        speed = get_rotation_speed(NFRAMES, fps, ANGLE)

        print(f"FPS: {fps}")
        print(f"Speed: {speed} degree/s")

        # Setup rotational stage
        zaber_conn, axis = setup_zaber(PORT)

        print("Setup rotation stage")

        # Grab full scene
        rotate_relative(axis, ANGLE, speed)

        scene = grab_hyperspectral_scene(
            cam, NFRAMES, white_image, dark_image, "speed_test"
        )

        print("Plotting RGB Image...")
        plt.figure()

        # Get indices of RGB bands from calibration file
        RGB = (
            get_wavelength_index(cal_arr, 690, pixel_binning),
            get_wavelength_index(cal_arr, 535, pixel_binning),
            get_wavelength_index(cal_arr, 470, pixel_binning),
        )

        plt.imshow(scene[:, :, RGB])

        # Return to initial position
        rotate_relative(axis, -ANGLE, 40)

        # Close Connections
        zaber_conn.close()
        cam.Close()

    except Exception as e:
        print(e)
        cam.Close()
        zaber_conn.close()
        print("ALL CONNECTIONS CLOSED")


if __name__ == "__main__":

    # General parameters
    CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
    PORT = "COM7"  # CHANGE PER USER
    ANGLE = 27

    # Camera parameters
    NFRAMES = 1600
    pixel_binning = 2
    NFRAMES = 1600 / pixel_binning
    exposure_time = 10000
    cam_gain = 500

    take_hyperspectral_image(PORT, NFRAMES, ANGLE, CALIBRATION_FILE_PATH)
