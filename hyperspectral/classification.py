import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
from scipy.ndimage import median_filter, generic_filter
from scipy.stats import mode
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


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


def mode_filter(image, size=100):
    """
    Applies a mode filter, replacing each pixel with the most common value in its neighborhood.
    """
    return generic_filter(
        image, lambda x: mode(x, axis=None)[0], size=(size, size)
    )


def morphological_smoothing(image, kernel_size=100):
    """
    Uses morphological operations to smooth the classification output:
    - Closing removes small holes
    - Opening removes small isolated pixels
    """
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    closed = cv2.morphologyEx(image.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
    return image


def classify_and_visualise(
    image, labels, model, selected_bands, filter_size=3
):
    """Classifies an image, smooths results, and visualizes predictions."""
    h, w, _ = image.shape
    image_selected = image[:, :, selected_bands]

    # Predict per pixel
    predictions = model.predict(
        image_selected.reshape(-1, len(selected_bands))
    )
    predicted_labels = predictions.reshape(h, w)

    # Plot the results
    fig, axes = plt.subplots(1, 4, figsize=(16, 6))

    sns.heatmap(labels, cmap="jet", square=True, cbar=False, ax=axes[0])
    axes[0].set_title("Original Labels")

    sns.heatmap(
        predicted_labels, cmap="jet", square=True, cbar=False, ax=axes[1]
    )
    axes[1].set_title("Predicted Labels (Before Smoothing)")

    sns.heatmap(
        predicted_labels, cmap="jet", square=True, cbar=False, ax=axes[2]
    )
    axes[2].set_title("Mode Filtered Labels")

    plt.show()


def test(sample):
    """Loads a sample hyperspectral image and applies classification."""
    image_path = os.path.join(images_folder, sample + ".npy")
    label_path = os.path.join(images_folder, sample, "label.png")

    if os.path.exists(image_path) and os.path.exists(label_path):
        image = np.load(image_path)
        labels = plt.imread(label_path)

        if len(labels.shape) == 3:
            labels = labels[:, :, 0]

        classify_and_visualise(
            image, labels, clf, selected_bands, filter_size=3
        )
    else:
        print(f"{sample} not found.")


if __name__ == "__main__":
    images_folder = "images/outdoor_dataset"
    label_encoding_path = os.path.join(images_folder, "label_encoding.npy")

    # Load label encoder
    label_encoder = load_label_encoder(label_encoding_path)
    label_decoder = {v: k for k, v in label_encoder.items()}

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

    # Evaluate model
    y_pred = clf.predict(X_test)
    print(f"Random Forest Accuracy: {accuracy_score(y_test, y_pred):.4f}")

    # **Loop through all subdirectories and test each**
    for sample in os.listdir(images_folder):
        sample_path = os.path.join(images_folder, sample)
        if os.path.isdir(sample_path):  # Only process directories
            print(f"Processing sample: {sample}")
            test(sample)
