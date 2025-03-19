import os
import numpy as np
from PIL import Image


def create_label_encoder(
    images_folder, save_path="label_encoding.npy", min_samples=100
):
    """
    Creates a label encoder mapping original class labels to encoded values and class names.

    Parameters:
        images_folder (str): Path to the dataset directory containing subfolders with labeled images.
        save_path (str): Path to save the label encoding file.
        min_samples (int): Minimum required pixel samples for a class to be saved.
                            (this is to handle a labelme nuance)

    Returns:
        dict: Label encoder mapping original label -> (encoded label, class name).
    """

    label_encoder = {}  # Maps original label -> (encoded label, class name)

    # Iterate through dataset subfolders
    for subfolder in os.listdir(images_folder):
        subfolder_path = os.path.join(images_folder, subfolder)
        if not os.path.isdir(subfolder_path):
            continue  # Skip if not a valid directory

        # Delete existing class_x.npy files
        for file in os.listdir(subfolder_path):
            if file.startswith("class_") and file.endswith(".npy"):
                file_path = os.path.join(subfolder_path, file)
                os.remove(file_path)
                print(f"Deleted: {file_path}")

        # Load label mask (grayscale) using PIL
        label_mask_path = os.path.join(subfolder_path, "label.png")
        label_mask = np.asarray(Image.open(label_mask_path))

        # Load corresponding hyperspectral image
        npy_path = os.path.join(images_folder, subfolder + ".npy")
        hyperspectral_image = np.load(npy_path)  # Shape: (H, W, Bands)

        # Load class names
        label_names_path = os.path.join(subfolder_path, "label_names.txt")
        with open(label_names_path, "r") as f:
            class_name_list = [line.strip() for line in f.readlines()]

        # Get unique labels from mask (excluding 0which is the background i.e. unlabelled)
        unique_labels = sorted(
            [label for label in np.unique(label_mask) if label != 0]
        )

        # Create mapping from original label to new encoded labels starting at 0
        label_mapping = {
            orig_label: new_label
            for new_label, orig_label in enumerate(unique_labels)
        }

        for orig_label, new_label in label_mapping.items():
            class_name = (
                class_name_list[orig_label]
                if orig_label < len(class_name_list)
                else f"Unknown_{orig_label}"
            )
            label_encoder[new_label] = (new_label, class_name)

            # Extract pixels corresponding to this label
            mask = label_mask == orig_label
            class_pixels = hyperspectral_image[mask]

            # Save if enough samples exist (labelme nuance)
            if class_pixels.shape[0] >= min_samples:
                save_class_path = os.path.join(
                    subfolder_path, f"class_{new_label}.npy"
                )
                np.save(save_class_path, class_pixels)
                print(
                    f"Saved: {save_class_path} (Original Label: {orig_label} -> Encoded: {new_label}, Name: {label_encoder[new_label][1]}, Samples: {class_pixels.shape[0]})"
                )
            else:
                print(
                    f"Skipped saving class_{new_label}.npy (Only {class_pixels.shape[0]} samples)"
                )

    # Save the label encoding dictionary
    save_encoding_path = os.path.join(images_folder, save_path)
    np.save(save_encoding_path, label_encoder)
    print(f"Label encoding saved at {save_encoding_path}")

    return label_encoder  # Return the mapping


images_folder = "images/outdoor_dataset_limited"
label_encoder = create_label_encoder(images_folder)
