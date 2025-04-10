# Common Imports
import os
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from collections import Counter
import json

# Image Imports
from PIL import Image
import cv2
from scipy.ndimage import median_filter

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam, RMSprop, SGD
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau


def set_seed(seed=42):
    """Fix seed for reporducibility"""

    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


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


def subsample_data(X, y, N=200000, plot=True):
    """Subsamples N random samples from the dataset while maintaining class proportions.

    If `plot=True` plos class distributions before and after subsampling
    """

    unique_classes, class_counts = np.unique(y, return_counts=True)
    total_samples = X.shape[0]

    if plot:
        # Plot original class distribution
        plt.figure(figsize=(10, 4))
        plt.bar(unique_classes, class_counts, tick_label=unique_classes)
        plt.xlabel("Class Labels")
        plt.ylabel("Sample Count")
        plt.title("Original Class Distribution")
        plt.show()

    # % of each class
    class_proportions = class_counts / total_samples

    # no of each class to maintain
    subsample_counts = (class_proportions * N).astype(int)

    X_subsampled, y_subsampled = [], []

    for unique_class, count in zip(unique_classes, subsample_counts):
        # Get indices of current class
        class_indices = np.where(y == unique_class)[0]

        # Randomly sample from this class
        sampled_indices = np.random.choice(class_indices, count, replace=False)

        X_subsampled.append(X[sampled_indices])
        y_subsampled.append(y[sampled_indices])

    X_subsampled, y_subsampled = np.vstack(X_subsampled), np.hstack(
        y_subsampled
    )

    if plot:
        # Plot subsampled class distribution
        subsampled_counts = Counter(y_subsampled)
        plt.figure(figsize=(10, 4))
        plt.bar(
            subsampled_counts.keys(),
            subsampled_counts.values(),
            tick_label=subsampled_counts.keys(),
        )
        plt.xlabel("Class Labels")
        plt.ylabel("Sample Count")
        plt.title("Subsampled Class Distribution")
        plt.show()

    return X_subsampled, y_subsampled


def train_neural_network(
    X_train,
    y_train,
    X_val,
    y_val,
    input_shape,
    num_classes,
    epochs=125,
    batch_size=32,
    optimizer_choice="adam",
    activation="relu",
    dropout_rate=0.3,
    l2_reg=0.001,
    num_layers=3,
    neurons_per_layer=[64, 128, 64],
    random_search=False,
    num_random_searches=15,
    loss_function="sparse_categorical_crossentropy",
    metrics=["accuracy"],
    lr=0.001,  # Learning rate is now tunable
):
    """Trains a  neural network with flag to random search for hyperparameter tuning."""

    results = []

    for search in range(num_random_searches if random_search else 1):
        # Generate random hyperparameters
        if random_search:
            num_layers = random.choice([2, 3, 4, 5])
            neurons_per_layer = [
                random.choice([32, 64, 128, 256]) for _ in range(num_layers)
            ]
            dropout_rate = random.choice([0.2, 0.3, 0.4, 0.5])
            l2_reg = random.choice([1e-2, 1e-3, 1e-4])
            optimizer_choice = random.choice(["adam", "rmsprop", "sgd"])
            lr = random.choice(
                [1e-2, 1e-3, 1e-4]
            )  # Random learning rate selection
            batch_size = random.choice([32, 64, 128])

        # Print selected hyperparameters
        print(
            f"\n🔍 **Search {search + 1}/{num_random_searches} - Selected Hyperparameters:**"
        )
        print(f"  - Layers: {num_layers}")
        print(f"  - Neurons per Layer: {neurons_per_layer}")
        print(f"  - Dropout Rate: {dropout_rate}")
        print(f"  - L2 Regularization: {l2_reg}")
        print(f"  - Optimizer: {optimizer_choice}")
        print(f"  - Learning Rate: {lr}")
        print(f"  - Batch Size: {batch_size}")

        # Build model
        model = Sequential()
        model.add(Input(shape=(input_shape,)))

        for i in range(1, num_layers):
            model.add(
                Dense(
                    neurons_per_layer[i],
                    activation=activation,
                    kernel_regularizer=l2(l2_reg),
                )
            )
            model.add(BatchNormalization())
            model.add(Dropout(dropout_rate))

        model.add(Dense(num_classes, activation="softmax"))

        # Define optimiser obj
        optimizers = {
            "adam": Adam(learning_rate=lr),
            "rmsprop": RMSprop(learning_rate=lr),
            "sgd": SGD(learning_rate=lr, momentum=0.9),
        }
        optimizer = optimizers.get(optimizer_choice, Adam(learning_rate=lr))

        # Compile model
        model.compile(optimizer=optimizer, loss=loss_function, metrics=metrics)

        # Callbacks
        early_stopping = EarlyStopping(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True,
            verbose=1,
        )
        reduce_lr = ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
        )

        # Train model
        history = model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            callbacks=[early_stopping, reduce_lr],
        )

        # Evaluate model
        val_loss, val_acc = model.evaluate(X_val, y_val, verbose=1)

        # Store results
        results.append(
            {
                "search_id": search + 1,
                "num_layers": num_layers,
                "neurons_per_layer": neurons_per_layer,
                "dropout_rate": dropout_rate,
                "l2_reg": l2_reg,
                "optimizer": optimizer_choice,
                "learning_rate": lr,
                "batch_size": batch_size,
                "val_loss": round(val_loss, 4),
                "val_accuracy": round(val_acc, 4),
                "model": model,  # Store the model itself
            }
        )

        print(
            f"✅ Search {search + 1}/{num_random_searches}: Val Loss = {val_loss:.4f}, Val Acc = {val_acc:.4f}\n"
        )

    # Find the best model based on val accuracy
    best_model_data = max(results, key=lambda x: x["val_accuracy"])

    print("\n🏆 **Best Model Hyperparameters:**")
    for key, value in best_model_data.items():
        if key != "model":
            print(f"  - {key}: {value}")

    # Return best model and list of dict containing all results
    return best_model_data["model"], results


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
    predictions = np.argmax(predictions, axis=1)
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
            image, labels, best_model, selected_bands, label_encoder
        )
    else:
        print(f"{sample} not found.")


if __name__ == "__main__":

    set_seed()

    images_folder = "images/training_dataset"

    label_encoder_path = os.path.join(images_folder, "label_encoding.npy")
    label_encoder = load_label_encoder(label_encoder_path)

    # Select spectral bands
    selected_bands = select_bands()

    # Load and preprocess dataset
    X, y = load_dataset(images_folder, selected_bands)
    X, y = subsample_data(X, y)

    X = X / np.max(X)

    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Dataset shape: {X.shape}, Labels shape: {y.shape}")
    print(f"Train size: {X_train.shape}, Test size: {X_test.shape}")

    # Train the model
    num_classes = len(np.unique(y))  # Number of unique classes

    print(np.max(X_train))
    best_model, results = train_neural_network(
        X_train,
        y_train,
        X_test,
        y_test,
        input_shape=X.shape[1],
        num_classes=num_classes,
    )

    # Save the trained model
    best_model.save("NN_09_04_2025_v3.keras")

    # Remove model object which prevents writing to the jSon file
    results_json = [
        {k: v for k, v in result.items() if k != "model"} for result in results
    ]

    # Save results to JSON
    with open("random_search_results_3.json", "w") as f:
        json.dump(results_json, f, indent=4)

    print("Results saved to results.json successfully!")

    # Evaluate model
    y_pred = best_model.predict(X_test)
    y_pred = np.argmax(y_pred, axis=1)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")

    # **Loop through all subdirectories and test each**
    for sample in os.listdir(images_folder):
        sample_path = os.path.join(images_folder, sample)
        if os.path.isdir(sample_path):  # Only process directories

            print(f"Processing sample: {sample}")
            # plot_correlation_heatmap(sample)
            test(sample)
