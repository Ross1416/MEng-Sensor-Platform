import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from scipy.ndimage import median_filter
import matplotlib.colors as mcolors
from hyperspectral_driver import get_wavelength_index, get_calibration_array


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


def calculated_ndvi(full_image):
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


def classify_and_save(
    model_path, image_path, label_encoding_path, output_path
):

    output_name, _ = os.path.splitext(output_path)

    # Load model
    model = tf.keras.models.load_model(model_path)

    # Load hyperspectral image (full image for NDVI)
    full_image = np.load(image_path)

    # Keep the reduced image for classification
    selected_band_indices = select_bands()
    image = full_image[:, :, selected_band_indices]  # reduced image

    h, w, num_bands = image.shape
    image_reshaped = image.reshape(-1, num_bands)  # Flatten for model input

    # Classify image
    predictions = model.predict(image_reshaped)
    predicted_labels = np.argmax(predictions, axis=1)
    classified_image = predicted_labels.reshape(h, w)

    # Apply smoothing (using median filter)
    smoothed_image = apply_smoothing(classified_image)

    # Load label encoder
    label_encoder = load_label_encoder(label_encoding_path)

    # Calculate NDVI
    ndvi = calculated_ndvi(full_image)

    # Saving the image
    output_path = output_name + "_ndvi.png"
    plt.figure(figsize=(8, 6))
    plt.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    plt.colorbar(label="NDVI")
    plt.title("NDVI Across Entire Image")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"NDVI image saved as {output_path}")

    # Extract unique classes and their counts
    unique_classes, counts = np.unique(smoothed_image, return_counts=True)
    total_pixels = smoothed_image.size

    # Compute percentage of each class
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
    img = plt.imshow(
        smoothed_image,
        cmap=custom_cmap,
        vmin=unique_classes[0],
        vmax=unique_classes[-1],
    )
    plt.title("Smoothed Classification Results")

    # Add colorbar legend
    cbar = plt.colorbar(img, ticks=list(legend_labels.keys()))
    cbar.set_ticklabels(list(legend_labels.values()))
    cbar.set_label("Class Labels")

    # Save output image
    output_path = output_name + "_classification.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Smoothed classification results saved to {output_path}")

    return class_percentages


if __name__ == "__main__":

    CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
    cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)

    model_path = "NN_18_03_2025.keras"
    image_path = "images/outdoor_dataset_limited/outdoor_dataset_005.npy"
    label_encoding_path = "images/outdoor_dataset_limited/label_encoding.npy"
    output_name = "test.png"

    class_distribution = classify_and_save(
        model_path, image_path, label_encoding_path, output_name
    )
    print("Class Distribution (%):", class_distribution)
