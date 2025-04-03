import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from scipy.ndimage import median_filter
import matplotlib.colors as mcolors
from hyperspectral_driver import (
    get_wavelength_index,
    get_calibration_array,
)


def select_bands(start=100, end=500, num_bands=30):
    """Selects a specified number of uniformly distributed spectral bands."""
    return np.linspace(start, end - 1, num_bands, dtype=int)


def load_label_encoder(label_encoding_path):
    """Loads the label encoder from a file."""
    if os.path.exists(label_encoding_path):
        return np.load(label_encoding_path, allow_pickle=True).item()
    raise FileNotFoundError("Label encoding file not found!")


def apply_smoothing(image, filter_size=10):
    """Applies median filtering to reduce speckling noise in classification results."""
    return median_filter(image, size=filter_size)


def calculated_ndvi(full_image, cal_arr):
    """Calculated NDVI for all pixels in the image"""

    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 800, 2)

    # Extract Red and NIR bands
    red_band = (full_image[:, :, red_idx]).astype(np.float32)
    nir_band = (full_image[:, :, nir_idx]).astype(np.float32)

    # Avoid divide-by-zero
    denominator = nir_band + red_band

    # Compute NDVI
    ndvi = (nir_band - red_band) / denominator

    return ndvi


def calculate_ndmi(full_image, cal_arr):

    nir_idx = get_wavelength_index(cal_arr, 800, 2)
    swir_idx = get_wavelength_index(cal_arr, 1050, 2)

    # Extract NIR and SWIR bands
    nir_band = (full_image[:, :, nir_idx]).astype(np.float32)
    swir_band = (full_image[:, :, swir_idx]).astype(np.float32)

    denominator = nir_band + swir_band

    ndmi = (nir_band - swir_band) / denominator

    return ndmi


def classify_and_save(
    model_path, full_image, label_encoding_path, output_path, cal_arr
):

    output_name, _ = os.path.splitext(output_path)

    # Load model
    model = tf.keras.models.load_model(model_path)

    # Load hyperspectral image (full image for NDVI)
    full_image = np.load(image_path)

    # Load label encoder
    # label_encoder = load_label_encoder(label_encoding_path)

    # Calculate NDVI
    ndvi = calculated_ndvi(full_image, cal_arr)

    # Calculate NDMI
    ndmi = calculate_ndmi(full_image, cal_arr)

    # Saving the image
    output_path = output_name + "_ndvi.png"
    plt.figure(figsize=(8, 6), facecolor="black")
    ax = plt.gca()
    ax.set_facecolor("black")
    im = plt.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    cbar = plt.colorbar(im, label="NDVI")
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(color="white", labelcolor="white")
    plt.title("NDVI", color="white")
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="black")
    plt.close()
    print(f"NDVI image saved as {output_path}")

    # Saving the image
    output_path = output_name + "_ndmi.png"
    plt.figure(figsize=(8, 6), facecolor="black")
    ax = plt.gca()
    ax.set_facecolor("black")
    im = plt.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    cbar = plt.colorbar(im, label="NDMI")
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(color="white", labelcolor="white")
    plt.title("NDMI", color="white")
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="black")
    plt.close()
    print(f"NDMI image saved as {output_path}")

    return ndmi


if __name__ == "__main__":

    CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
    cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)

    model_path = "NN_18_03_2025.keras"
    image_path = "images/outdoor_dataset_limited/outdoor_dataset_005.npy"
    label_encoding_path = "images/outdoor_dataset_limited/label_encoding.npy"
    output_name = "test.png"

    x = classify_and_save(
        model_path, image_path, label_encoding_path, output_name, cal_arr
    )
    # print("Class Distribution (%):", class_distribution)
