# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 13:28:55 2025

@author: Chris
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from hyperspectral_driver import *


def npy_to_png(class_name):

    # Define path
    folder = f"images/{class_name}"

    cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)

    # Get indices of RGB bands from calibration file
    RGB = (
        get_wavelength_index(cal_arr, 690, 2),
        get_wavelength_index(cal_arr, 535, 2),
        get_wavelength_index(cal_arr, 470, 2),
    )

    # Loop through files in the input folder
    for file in os.listdir(folder):
        if file.startswith(class_name) and file.endswith(".npy"):
            file_path = os.path.join(folder, file)

            # Load hyperspectral .npy file
            hyperspectral_image = np.load(
                file_path
            )  # Shape: (Height, Width, Bands)

            # Extract RGB approximation
            rgb_image = hyperspectral_image[:, :, RGB]

            # rgb_image = (rgb_image - np.min(rgb_image)) / (np.max(rgb_image) - np.min(rgb_image))

            # Save as PNG
            output_path = os.path.join(folder, file.replace(".npy", ".png"))
            plt.imsave(output_path, rgb_image)
            print(f"Saved {output_path}")

    print("All hyperspectral images have been converted and saved.")


if __name__ == "__main__":

    CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
    CLASS_NAME = "outdoor_dataset"

    npy_to_png(class_name=CLASS_NAME)
