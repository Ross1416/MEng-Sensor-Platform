from zaber_driver import *
from hyperspectral_driver import *
import matplotlib.pyplot as plt
import os


def take_hyperspectral_image(PORT, nframe, angle, calibration):

    try:
        # Get Calibration
        cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)
        # print(get_wavelength_index(calibration_array,450,1))

        # Setup hyperspectral
        cam = setup_hyperspectral()
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
        print(f"Speed: {speed} degree/s")

        # Setup rotational stage
        zaber_conn, axis = setup_zaber(PORT)

        print("Setup rotation stage")

        # Grab full scene
        rotate_relative(axis, ANGLE, speed)

        scene = grab_hyperspectral_scene(
            cam, NFRAMES, white_image, dark_image, "outdoor_dataset"
        )

        print("Plotting RGB Image...")
        plt.figure()

        # Get indices of RGB bands from calibration file
        RGB = (
            get_wavelength_index(cal_arr, 690, 2),
            get_wavelength_index(cal_arr, 535, 2),
            get_wavelength_index(cal_arr, 470, 2),
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
    CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
    PORT = "COM7"  # CHANGE PER USER
    NFRAMES = 800
    ANGLE = 27

    take_hyperspectral_image(PORT, NFRAMES, ANGLE, CALIBRATION_FILE_PATH)
