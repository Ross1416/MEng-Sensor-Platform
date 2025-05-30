import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from scipy.ndimage import median_filter
import matplotlib.colors as mcolors
import logging
from hyperspectral.hyperspectral_driver import (
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


def plot_and_save_index(
    index_data, output_path, manual_flag, title="Index", cmap="RdYlGn", vmin=-1, vmax=1
):
    """
    Plots and saves a vegetation index image
    """

    plt.figure(figsize=(8, 6))
    plt.axis("off")
    im = plt.imshow(index_data, cmap=cmap, vmin=vmin, vmax=vmax)

    if not manual_flag:
        plt.axis("off")
        ax = plt.gca()
        ax.set_facecolor("black")

        cbar = plt.colorbar(im, label=title)
        cbar.ax.yaxis.label.set_color("white")
        cbar.ax.tick_params(color="white", labelcolor="white")
        plt.title(title, color="white")

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True,
    )
    plt.close()
    print(f"{title} image saved as {output_path}")


def calculate_ndvi(full_image, cal_arr):
    """Calculate NDVI for all pixels in the image."""
    logging.debug("Calculating NDVI")
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)

    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)

    denominator = nir_band + red_band
    ndvi = (nir_band - red_band) / denominator

    # Replace NaNs and Infs with 0
    ndvi = np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)
    logging.debug("Succesfully calculated NDVI")
    return ndvi

def calculate_msavi(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    msavi = 0.5*(2*(nir_band+1)-np.sqrt((2*nir_band+1)**2-8*(nir_band-red_band)))
    return np.nan_to_num(msavi, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom1(full_image, cal_arr):
    a = get_wavelength_index(cal_arr, 700, 2)
    b = get_wavelength_index(cal_arr, 770, 2)
    a = full_image[:, :, a].astype(np.float32)
    b = full_image[:, :, b].astype(np.float32)
    result = 5*((b - a) / (b + a))
    result = np.clip(result, -1, 1)
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom2(full_image, cal_arr):
    a = get_wavelength_index(cal_arr, 540, 2)
    b = get_wavelength_index(cal_arr, 580, 2)
    a = full_image[:, :, a].astype(np.float32)
    b = full_image[:, :, b].astype(np.float32)
    result = np.clip((6*(b - a) / (b + a)),-1,1)
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom4(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 820, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    result = 2*(nir_band - red_band) / (nir_band + red_band)
    result = np.clip(result, -1, 1)
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom_artifical(full_image, cal_arr):
    custom1 = calculate_custom1(full_image, cal_arr)
    custom2 = calculate_custom2(full_image, cal_arr)
    custom4 = calculate_custom4(full_image, cal_arr)
    ndvi = calculate_ndvi(full_image, cal_arr)
    # result = np.where(ndvi < -0.4, ndvi, custom2)# + np.where(ndvi < -0.4, -1, 0) #+ np.where(custom1 < 0.1, -1, 0) + np.where(custom2 < -0.5, -1, 0)
    result = np.where(custom4 < -0.55, custom4, np.where(custom1 < -0.4, custom1,custom2))
    # result = np.where(custom1 < -0.4, custom1, custom2)
    result = np.clip(result, -1, 1)
    return np.nan_to_num(np.clip(result,-1,1), nan=0.0, posinf=0.0, neginf=0.0)

def calculate_pi(full_image, cal_arr):
    """ """
    logging.debug("Calculating PI")
    r680 = get_wavelength_index(cal_arr, 680, 2)
    r750 = get_wavelength_index(cal_arr, 750, 2)
    r860 = get_wavelength_index(cal_arr, 860, 2)

    band_680 = full_image[:, :, r680].astype(np.float32)
    band_750 = full_image[:, :, r750].astype(np.float32)
    band_860 = full_image[:, :, r860].astype(np.float32)

    # Spectral contrast: if the curve is flat, it might be plastic
    pi = 1 - (np.abs(band_750 - band_680) + np.abs(band_860 - band_750)) / (
        band_680 + band_860 + 1e-6
    )

    pi = np.nan_to_num(pi, nan=0.0, posinf=0.0, neginf=0.0)
    logging.debug("Succesfully calculated PI")
    return pi


def classify_and_save(
    model_path, full_image, label_encoding_path, output_path, cal_arr, manual_flag
):
    logging.debug("Classifying hyperspectral scene")
    output_name, _ = os.path.splitext(output_path)

    # Load model
    logging.debug("Loading classification model")
    model = tf.keras.models.load_model(model_path)
    logging.debug("Successfully loaded classification model")

    # Load hyperspectral image (full image for NDVI)
    # full_image = np.load(image_path)

    # Keep the reduced image for classification
    selected_band_indices = select_bands()
    image = full_image[:, :, selected_band_indices]  # reduced image
    image = image / np.max(image)
    # image = normalize_image(image)

    h, w, num_bands = image.shape
    image_reshaped = image.reshape(-1, num_bands)  # Flatten for model input

    # Classify image
    logging.debug("Classifying materials in scene")
    predictions = model.predict(image_reshaped)
    predicted_labels = np.argmax(predictions, axis=1)
    classified_image = predicted_labels.reshape(h, w)
    logging.debug("Finished classifying materials")

    # Apply smoothing (using median filter)
    logging.debug("Smoothing classification result")
    smoothed_image = apply_smoothing(classified_image)
    logging.debug("Successfully finished smoothing classification result")

    # Load label encoder
    label_encoder = load_label_encoder(label_encoding_path)

    # Extract unique classes and their counts
    unique_classes, counts = np.unique(smoothed_image, return_counts=True)
    total_pixels = smoothed_image.size

    # Compute percentage of each class
    logging.debug("Computing material classification distribution")
    class_percentages = {
        label_encoder[orig][1]: (counts[i] / total_pixels) * 100
        for i, orig in enumerate(unique_classes)
    }

    # Generate colormap
    cmap = plt.get_cmap("gist_rainbow", len(unique_classes))
    colors = cmap(np.linspace(0, 1, len(unique_classes)))
    custom_cmap = mcolors.ListedColormap(colors)

    # Generate legend mapping from encoded labels to class names
    legend_labels = {
        encoded: label_encoder[orig][1]
        for orig, (encoded, _) in label_encoder.items()
        if encoded in unique_classes
    }

    # Plot classification result
    plt.figure(figsize=(8, 6))
    plt.axis("off")
    # ax = plt.gca()
    # ax.set_facecolor("black")
    img = plt.imshow(
        smoothed_image,
        cmap=custom_cmap,
        vmin=unique_classes[0],
        vmax=unique_classes[-1],
    )

    if not manual_flag:

        ax = plt.gca()
        ax.set_facecolor("black")

        plt.title("Material Classification", color="white")

        # Add colorbar legend
        cbar = plt.colorbar(img, ticks=list(legend_labels.keys()))
        cbar.set_ticklabels(list(legend_labels.values()))
        cbar.set_label("Class Labels", color="white")
        cbar.ax.tick_params(color="white", labelcolor="white")

    # Save output image
    output_path = output_name + "_classification.png"
    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True,
    )
    plt.close()
    logging.debug(f"Smoothed classification results saved to {output_path}")

    """
    Calculate Indices
    """

    logging.debug("Calculating NDVI...")
    ndvi = calculate_ndvi(full_image, cal_arr)
    logging.debug("Calculating MSAVI...")
    masavi = calculate_msavi(full_image, cal_arr)
    logging.debug("Calculating CUSTOM2 Index...")
    custom2 = calculate_custom2(full_image, cal_arr)
    logging.debug("Calculating ARTIFICIAL index...")
    artificial = calculate_custom_artifical(full_image, cal_arr)

    plot_and_save_index(
        ndvi,
        output_name + "_ndvi.png",
        manual_flag=manual_flag,
        title="NDVI",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
    )

    plot_and_save_index(
        masavi,
        output_name + "_msavi.png",
        manual_flag=manual_flag,
        title="MSAVI",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
    )

    plot_and_save_index(
        custom2,
        output_name + "_custom2.png",
        manual_flag=manual_flag,
        title="CUSTOM2",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
    )

    plot_and_save_index(
        artificial,
        output_name + "_artificial.png",
        manual_flag=manual_flag,
        title="ARTIFICIAL",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
    )

    return class_percentages


if __name__ == "__main__":

    CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
    cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)

    model_path = "NN_09_04_2025_v3.keras"
    image_path = "debug_PiB/scene_8.npy"
    label_encoding_path = "images/training_dataset/label_encoding.npy"
    output_name = "test.png"

    full_image = np.load(image_path)

    class_distribution = classify_and_save(
        model_path, full_image, label_encoding_path, output_name, cal_arr
    )
    # print("Class Distribution (%):", class_distribution)
