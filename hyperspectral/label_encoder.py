import os
import numpy as np
import cv2

# Define paths
images_folder = "images/outdoor_dataset"

# Dictionary to encode class labels
label_encoder = {}
label_names = {}  # Stores the mapping from encoded label to class name
current_label = 0

# Each subfolder contains a labeled image
for subfolder in os.listdir(images_folder):
    subfolder_path = os.path.join(images_folder, subfolder)

    # Skip if not a directory
    if not os.path.isdir(subfolder_path):
        continue

    # Load the label mask
    label_mask_path = os.path.join(subfolder_path, "label.png")

    # Load corresponding .npy file
    npy_path = os.path.join(images_folder, subfolder + ".npy")

    # Load label names
    label_names_path = os.path.join(subfolder_path, "label_names.txt")
    if os.path.exists(label_names_path):
        with open(label_names_path, "r") as f:
            class_name_list = [
                line.strip() for line in f.readlines()[1:]
            ]  # Skip first line
    else:
        class_name_list = []

    # The data
    label_mask = cv2.imread(label_mask_path, cv2.IMREAD_GRAYSCALE)
    hyperspectral_image = np.load(npy_path)  # Shape: (H, W, Bands)

    # Get unique labels and encode each of them
    unique_labels = np.unique(label_mask)
    for label in unique_labels:
        if label == 0:
            continue  # Skip background pixels

        # New label if not already assigned
        if label not in label_encoder:
            label_encoder[label] = current_label

            # Assign class name if available
            class_name = (
                class_name_list[current_label]
                if current_label < len(class_name_list)
                else f"Unknown_{current_label}"
            )
            label_names[current_label] = class_name

            current_label += 1

        # Get pixels corresponding to this label
        mask = label_mask == label
        class_pixels = hyperspectral_image[mask]

        # Only save if there are at least 100 samples
        if class_pixels.shape[0] >= 100:
            save_path = os.path.join(
                subfolder_path, f"class_{label_encoder[label]}.npy"
            )
            np.save(save_path, class_pixels)
            print(
                f"Saved: {save_path} (Original Label: {label} -> Encoded as: {label_encoder[label]}, Name: {label_names[label_encoder[label]]}, Samples: {class_pixels.shape[0]})"
            )
        else:
            print(
                f"Skipped saving class_{label_encoder[label]}.npy (Only {class_pixels.shape[0]} samples)"
            )

# Save label encoding and class names for reference
encoding_data = label_encoder

encoding_path = os.path.join(images_folder, "label_encoding.npy")
np.save(encoding_path, encoding_data)
print(f"Label encoding saved at {encoding_path}")
