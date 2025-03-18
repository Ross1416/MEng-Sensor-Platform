import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
from scipy.ndimage import median_filter
from scipy.stats import mode
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from PIL import Image


def plot_correlation_heatmap(hyperspectral_image, selected_bands=None):
    """
    Plots a correlation heatmap for spectral bands in a hyperspectral image.

    Parameters:
        hyperspectral_image (numpy array): 3D array of shape (height, width, num_bands)
        selected_bands (list, optional): List of band indices to highlight.
    """
    # Reshape to (num_pixels, num_bands) for correlation computation
    h, w, num_bands = hyperspectral_image.shape
    reshaped_data = hyperspectral_image.reshape(-1, num_bands)

    # Compute the correlation matrix
    correlation_matrix = np.corrcoef(reshaped_data, rowvar=False)

    # Plot heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        correlation_matrix,
        cmap="coolwarm",
        annot=False,
        xticklabels=10,
        yticklabels=10,
    )
    plt.title("Spectral Band Correlation Heatmap")
    plt.xlabel("Spectral Band Index")
    plt.ylabel("Spectral Band Index")

    # Highlight selected bands if provided
    if selected_bands is not None:
        for band in selected_bands:
            plt.axvline(x=band, color="black", linestyle="--", alpha=0.5)
            plt.axhline(y=band, color="black", linestyle="--", alpha=0.5)

    plt.show()


def load_label_encoder(label_encoding_path):
    """Loads the label encoder from a file."""
    if os.path.exists(label_encoding_path):
        return np.load(label_encoding_path, allow_pickle=True).item()
    raise FileNotFoundError("Label encoding file not found!")


def select_bands(start=100, end=500, num_bands=30):
    """Selects a specified number of uniformly distributed spectral bands."""
    return np.linspace(start, end - 1, num_bands, dtype=int)


def load_dataset(images_folder, selected_bands):
    """Loads the dataset from saved class files."""
    X, y = [], []
    for subfolder in os.listdir(images_folder):
        subfolder_path = os.path.join(images_folder, subfolder)
        if not os.path.isdir(subfolder_path):
            continue

        for file in os.listdir(subfolder_path):

            if file.startswith("class_") and file.endswith(".npy"):
                class_label = int(file.split("_")[1].split(".")[0])
                data = np.load(os.path.join(subfolder_path, file))[
                    :, selected_bands
                ]
                X.append(data)
                y.append(np.full(len(data), class_label))

    return np.vstack(X), np.hstack(y)


def subsample_data(X, y, N=100000):
    """Subsamples N random samples from the dataset if necessary."""
    if X.shape[0] > N:
        idx = np.random.choice(X.shape[0], N, replace=False)
        return X[idx], y[idx]
    return X, y


def train_random_forest(X_train, y_train, n_estimators=100, random_state=42):
    """Trains a RandomForest classifier."""
    clf = RandomForestClassifier(
        n_estimators=n_estimators, random_state=random_state
    )
    clf.fit(X_train, y_train)
    return clf


def apply_smoothing(image, filter_size=10):
    """
    Applies median filtering to reduce speckling noise in classification results.
    """
    return median_filter(image, size=filter_size)


import matplotlib.colors as mcolors


def classify_and_visualise(
    image, labels, model, selected_bands, label_encoder, filter_size=5
):
    """Classifies an image, applies filtering, and visualizes the results with a legend."""

    h, w, _ = image.shape
    image_selected = image[:, :, selected_bands]

    # Predict per pixel
    predictions = model.predict(
        image_selected.reshape(-1, len(selected_bands))
    )
    predicted_labels = predictions.reshape(h, w)

    # Apply smoothing to results to reduce speckling noise
    smoothed_labels = apply_smoothing(predicted_labels, filter_size)

    # Extract unique classes
    unique_classes = np.unique(smoothed_labels)

    # Generate colormap
    num_classes = len(unique_classes)
    cmap = plt.get_cmap("gist_rainbow", num_classes)
    colors = cmap(np.arange(num_classes))
    custom_cmap = mcolors.ListedColormap(colors)

    # Generate legend mapping from encoded labels to class names
    legend_labels = {
        encoded: label_encoder[orig][1]
        for orig, (encoded, _) in label_encoder.items()
        if encoded in unique_classes
    }

    # Plot the results
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    # Original Labels
    img0 = axes[0].imshow(labels, cmap=custom_cmap)
    axes[0].set_title("Original Labels")

    # Raw Predictions
    img1 = axes[1].imshow(
        predicted_labels,
        cmap=custom_cmap,
        vmin=unique_classes[0],
        vmax=unique_classes[-1],
    )
    axes[1].set_title("Raw Predicted Labels")

    # Smoothed Predictions
    img2 = axes[2].imshow(
        smoothed_labels,
        cmap=custom_cmap,
        vmin=unique_classes[0],
        vmax=unique_classes[-1],
    )
    axes[2].set_title("Smoothed Predictions")

    # Add colorbar legend
    cbar = fig.colorbar(
        img2, ax=axes, orientation="horizontal", fraction=0.02, pad=0.1
    )
    cbar.set_ticks(list(legend_labels.keys()))
    cbar.set_ticklabels(list(legend_labels.values()))

    plt.show()


def test(sample):
    """Loads a sample hyperspectral image and applies classification."""
    image_path = os.path.join(images_folder, sample + ".npy")
    label_path = os.path.join(images_folder, sample, "label.png")

    if os.path.exists(image_path) and os.path.exists(label_path):
        image = np.load(image_path)
        labels = np.asarray(Image.open(label_path))

        if len(labels.shape) == 3:
            labels = labels[:, :, 0]

        classify_and_visualise(
            image, labels, clf, selected_bands, label_encoder
        )
    else:
        print(f"{sample} not found.")


if __name__ == "__main__":

    images_folder = "images/outdoor_dataset_limited"

    label_encoder_path = os.path.join(images_folder, "label_encoding.npy")
    label_encoder = load_label_encoder(label_encoder_path)

    # Select spectral bands
    selected_bands = select_bands()

    # Load and preprocess dataset
    X, y = load_dataset(images_folder, selected_bands)
    X, y = subsample_data(X, y)

    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Dataset shape: {X.shape}, Labels shape: {y.shape}")
    print(f"Train size: {X_train.shape}, Test size: {X_test.shape}")

    # Train the model
    clf = train_random_forest(X_train, y_train)

    # Save the trained model
    model_path = "RF_model.pkl"
    joblib.dump(clf, model_path)
    print(f"Model saved as {model_path}")

    # Evaluate model
    y_pred = clf.predict(X_test)
    print(f"Random Forest Accuracy: {accuracy_score(y_test, y_pred):.4f}")

    # **Loop through all subdirectories and test each**
    for sample in os.listdir(images_folder):
        sample_path = os.path.join(images_folder, sample)
        if os.path.isdir(sample_path):  # Only process directories

            print(f"Processing sample: {sample}")
            # plot_correlation_heatmap(sample)
            test(sample)
            break
