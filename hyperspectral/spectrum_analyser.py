import os
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog

from hyperspectral_driver import (
    get_wavelength_index,
    get_calibration_array,
)

# === Functions ===


def plot_and_save_index(
    index_data, output_path, title="Index", cmap="RdYlGn", vmin=-1, vmax=1
):
    plt.figure(figsize=(8, 6))
    plt.axis("off")
    im = plt.imshow(index_data, cmap=cmap, vmin=vmin, vmax=vmax)
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
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    return np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)


def save_spectrum(spectrum, label, x, y):
    header = ["file", "x", "y", "label"] + [f"{wl:.2f}" for wl in wavelengths]
    write_header = not os.path.exists(output_csv)

    with open(output_csv, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow([file_name, x, y, label] + list(spectrum))

    print(f"Saved labeled spectrum: ({x}, {y}) -> '{label}'")


# === Configuration ===

CALIBRATION_FILE_PATH = "calibration/BaslerPIA1600_CalibrationA.txt"
folder_path = "./debug_PiB"
output_csv = "labeled_spectra.csv"

root = tk.Tk()
root.withdraw()

# === Load Calibration and Files ===

cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)
npy_files = sorted(glob.glob(os.path.join(folder_path, "*.npy")))

if not npy_files:
    print("No .npy files found in the 'debug_PiB' folder.")
    exit()

print("Available hyperspectral files:")
for i, file in enumerate(npy_files):
    print(f"{i}: {os.path.basename(file)}")

while True:
    try:
        index = int(input(f"Select a file index (0–{len(npy_files)-1}): "))
        if 0 <= index < len(npy_files):
            break
        print("Index out of range.")
    except ValueError:
        print("Please enter a valid integer.")

file_path = npy_files[index]
file_name = os.path.basename(file_path)
print(f"Loading: {file_path}")

image_data = np.load(file_path)
if image_data.ndim != 3:
    print("Selected file is not a 3D hyperspectral cube.")
    exit()

# === Wavelengths ===

num_bands = image_data.shape[2]
binning_factor = len(cal_arr) // num_bands
wavelengths = cal_arr[::binning_factor][:num_bands]

# === Compute NDVI and Save ===

ndvi = calculate_ndvi(image_data, cal_arr)
ndvi_path = os.path.join(
    folder_path, f"{os.path.splitext(file_name)[0]}_ndvi.png"
)
plot_and_save_index(
    ndvi, ndvi_path, title="NDVI", cmap="RdYlGn", vmin=-1, vmax=1
)

# === RGB Image Creation ===

try:
    r_idx = get_wavelength_index(cal_arr, 650, 2)
    g_idx = get_wavelength_index(cal_arr, 550, 2)
    b_idx = get_wavelength_index(cal_arr, 450, 2)
except Exception as e:
    print("Error finding RGB band indices:", e)
    r_idx, g_idx, b_idx = 50, 30, 10  # Fallback

rgb_image = image_data[:, :, [r_idx, g_idx, b_idx]]
p_low, p_high = np.percentile(rgb_image, (1, 75))
rgb_image = np.clip(rgb_image, p_low, p_high)
rgb_image = ((rgb_image - p_low) / (p_high - p_low) * 255).astype(np.uint8)

# === NDVI Overlay (threshold < -0.5) ===

low_ndvi_mask = ndvi < -0.5
overlay_color = [255, 0, 0]  # Red
alpha = 0.5

rgb_overlay = rgb_image.copy()
for c in range(3):
    rgb_overlay[:, :, c] = np.where(
        low_ndvi_mask,
        (1 - alpha) * rgb_overlay[:, :, c] + alpha * overlay_color[c],
        rgb_overlay[:, :, c],
    )

rgb_overlay = rgb_overlay.astype(np.uint8)

# === Show & Save Overlay ===

plt.figure(figsize=(8, 6))
plt.imshow(rgb_overlay)
plt.title("RGB with NDVI < -0.5 Overlay")
plt.axis("off")
overlay_path = os.path.join(
    folder_path, f"{os.path.splitext(file_name)[0]}_ndvi_overlay.png"
)
plt.savefig(overlay_path, dpi=300, bbox_inches="tight", pad_inches=0.1)
plt.show()
print(f"NDVI overlay image saved as {overlay_path}")

# === Interactive Labeling ===

coords = []
fig, ax = plt.subplots()
ax.imshow(rgb_image)


def onclick(event):
    if event.inaxes != ax:
        return
    x, y = int(event.xdata), int(event.ydata)
    coords.append((x, y))
    spectrum = image_data[y, x, :]
    ax.plot(x, y, "rx")
    fig.canvas.draw()

    # Spectrum plot
    plt.figure()
    plt.plot(wavelengths, spectrum)
    plt.title(f"Spectrum at ({x}, {y})")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance / Intensity")
    plt.grid(True)
    plt.show()

    # Label prompt
    label = simpledialog.askstring(
        "Material Label", f"Label for point ({x}, {y}):"
    )
    if label:
        save_spectrum(spectrum, label.strip(), x, y)
    else:
        print("Label skipped, spectrum not saved.")


fig.canvas.mpl_connect("button_press_event", onclick)
plt.title("Click on points to view & label spectra")
plt.show()
