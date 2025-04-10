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

def calculate_gndvi(full_image, cal_arr):
    green_idx = get_wavelength_index(cal_arr, 560, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    green_band = full_image[:, :, green_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    ndvi = (nir_band - green_band) / (nir_band + green_band)
    return np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_ndwi(full_image, cal_arr):
    green_idx = get_wavelength_index(cal_arr, 560, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    green_band = full_image[:, :, green_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    ndwi = (green_band-nir_band) / (green_band+nir_band)
    return np.nan_to_num(ndwi, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_msavi(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    msavi = 0.5*(2*(nir_band+1)-np.sqrt((2*nir_band+1)**2-8*(nir_band-red_band)))
    return np.nan_to_num(msavi, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_pvi(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    a=0.6
    b=0.2
    pvi = (nir_band-a*red_band-b)/(np.sqrt(1+a**2))
    return np.nan_to_num(pvi, nan=0.0, posinf=0.0, neginf=0.0)

# Wide Dynamic Range Vegitation Index
def calculate_wdrvi(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    wdrvi = (0.1*nir_band - red_band) / (0.1*nir_band + red_band)
    return np.nan_to_num(wdrvi, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_npcri(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    blue_idx = get_wavelength_index(cal_arr, 492, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    blue_band = full_image[:, :, blue_idx].astype(np.float32)
    npcri = (red_band-blue_band) / (red_band+blue_band)
    return np.nan_to_num(npcri, nan=0.0, posinf=0.0, neginf=0.0)

# Green Chlorophyll Index
def calculate_clg(full_image, cal_arr):
    green_idx = get_wavelength_index(cal_arr, 680, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    green_band = full_image[:, :, green_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    clg = (nir_band/green_band)-1 # should be -1?
    return np.nan_to_num(clg, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_evi(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    blue_idx = get_wavelength_index(cal_arr, 470, 2)
    nir_idx = get_wavelength_index(cal_arr, 860, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    blue_band = full_image[:, :, blue_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    evi = 2.5*(nir_band-red_band)/(nir_band+6*red_band-7.5*blue_band+1)
    return np.nan_to_num(evi, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_ndbi(full_image, cal_arr):
    swir_idx = get_wavelength_index(cal_arr, 900, 2)
    nir_idx = get_wavelength_index(cal_arr, 800, 2)
    swir_band = full_image[:, :, swir_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    ndbi = (swir_band-nir_band)/(swir_band+nir_band)
    return np.nan_to_num(ndbi, nan=0.0, posinf=0.0, neginf=0.0)

# NIR edge
def calculate_custom1(full_image, cal_arr):
    a = get_wavelength_index(cal_arr, 700, 2)
    b = get_wavelength_index(cal_arr, 770, 2)
    a = full_image[:, :, a].astype(np.float32)
    b = full_image[:, :, b].astype(np.float32)
    custom1 = 5*((b - a) / (b + a))
    return np.nan_to_num(custom1, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom2(full_image, cal_arr):
    a = get_wavelength_index(cal_arr, 540, 2)
    b = get_wavelength_index(cal_arr, 580, 2)
    a = full_image[:, :, a].astype(np.float32)
    b = full_image[:, :, b].astype(np.float32)
    result = np.clip((6*(b - a) / (b + a)),-1,1)
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom3_sky(full_image, cal_arr):
    a = get_wavelength_index(cal_arr, 470, 2)
    b = get_wavelength_index(cal_arr, 530, 2)
    a = full_image[:, :, a].astype(np.float32)
    b = full_image[:, :, b].astype(np.float32)
    result = 6*((a - b) / (b + a))
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def calculate_custom1_2_combo(full_image, cal_arr):
    a = get_wavelength_index(cal_arr, 700, 2)
    b = get_wavelength_index(cal_arr, 770, 2)
    c = get_wavelength_index(cal_arr, 520, 2)
    d = get_wavelength_index(cal_arr, 560, 2)

    a = full_image[:, :, a].astype(np.float32)
    b = full_image[:, :, b].astype(np.float32)
    c = full_image[:, :, c].astype(np.float32)
    d = full_image[:, :, d].astype(np.float32)
    custom1 = ((b - a) / (b + a))
    custom2 = ((c - d) / (c + d))
    result = custom1+custom2
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

def calculate_custom4(full_image, cal_arr):
    red_idx = get_wavelength_index(cal_arr, 690, 2)
    nir_idx = get_wavelength_index(cal_arr, 820, 2)
    red_band = full_image[:, :, red_idx].astype(np.float32)
    nir_band = full_image[:, :, nir_idx].astype(np.float32)
    result = 2*(nir_band - red_band) / (nir_band + red_band)
    ndvi = np.clip(result, -1, 1)
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

def save_spectrum(spectrum, label, x, y):
    header = ["file", "x", "y", "label"] + [f"{wl:.2f}" for wl in wavelengths]
    write_header = not os.path.exists(output_csv)

    with open(output_csv, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow([file_name, x, y, label] + list(spectrum))

    print(f"Saved labeled spectrum: ({x}, {y}) -> '{label}'")

def quick_save(folder_path, file_name, index_data, name):
    path = os.path.join(
        folder_path, f"{os.path.splitext(file_name)[0]}_{name}.png"
    )
    plot_and_save_index(
        index_data, path, title=name.upper(), cmap="RdYlGn", vmin=-1, vmax=1
    )
# === Configuration ===

CALIBRATION_FILE_PATH = "hyperspectral/calibration/BaslerPIA1600_CalibrationA.txt"
folder_path = "./debug_PiB/"
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

# === Compute Indexes and Save ===

ndvi = calculate_ndvi(image_data, cal_arr)
gndvi = calculate_gndvi(image_data, cal_arr)
ndwi = calculate_ndwi(image_data, cal_arr)
msavi = calculate_msavi(image_data, cal_arr)
pvi = calculate_pvi(image_data, cal_arr)
npcri = calculate_npcri(image_data, cal_arr)
wdrvi = calculate_wdrvi(image_data, cal_arr) # poor
clg = calculate_clg(image_data, cal_arr)
evi = calculate_evi(image_data, cal_arr)
ndbi = calculate_ndbi(image_data, cal_arr)
custom1 = calculate_custom1(image_data, cal_arr)
custom2 = calculate_custom2(image_data, cal_arr)
custom1_2_combo = calculate_custom1_2_combo(image_data,cal_arr)
custom_artifical = calculate_custom_artifical(image_data,cal_arr)
custom3_sky = calculate_custom3_sky(image_data, cal_arr)
custom4 = calculate_custom4(image_data, cal_arr)

quick_save(folder_path, file_name, ndvi, "ndvi")
quick_save(folder_path, file_name, gndvi, "gndvi")
quick_save(folder_path, file_name, ndwi, "ndwi")
quick_save(folder_path, file_name, msavi, "msavi")
quick_save(folder_path, file_name, pvi, "pvi")
quick_save(folder_path, file_name, wdrvi, "wdrvi")
quick_save(folder_path, file_name, clg, "clg")
quick_save(folder_path, file_name, evi, "evi")
quick_save(folder_path, file_name, ndbi, "ndbi")
quick_save(folder_path, file_name, custom1, "custom1")
quick_save(folder_path, file_name, custom2, "custom2")
quick_save(folder_path, file_name, custom1_2_combo, "custom1_2_combo")
quick_save(folder_path, file_name, custom_artifical, "custom_artifical")
quick_save(folder_path, file_name, custom3_sky, "custom3_sky")
quick_save(folder_path, file_name, custom4, "custom4")

exit()

# === RGB Image Creation ===
try:
    r_idx = get_wavelength_index(cal_arr, 650, 2)
    g_idx = get_wavelength_index(cal_arr, 550, 2)
    b_idx = get_wavelength_index(cal_arr, 450, 2)
except Exception as e:
    print("Error finding RGB band indices:", e)
    r_idx, g_idx, b_idx = 50, 30, 10  # Fallback

rgb_image = image_data[:, :, [r_idx, g_idx, b_idx]]
p_low, p_high = np.percentile(rgb_image, (1, 90))
rgb_image = np.clip(rgb_image, p_low, p_high)
rgb_image = ((rgb_image - p_low) / (p_high - p_low) * 255).astype(np.uint8)

plt.figure(figsize=(8, 6))
plt.imshow(rgb_image)
plt.title(f"RGB")
plt.axis("off")
overlay_path = os.path.join(
    folder_path, f"{os.path.splitext(file_name)[0]}_rgb.png"
)
plt.savefig(overlay_path, dpi=300, bbox_inches="tight", pad_inches=0.1)
plt.show()

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

# === Custom 2 thresholding and overlay ===
threshold = -0.5
low_custom2_mask = custom_artifical < threshold
overlay_color = [255, 0, 0]  # Red
alpha =0.7

rgb_overlay = rgb_image.copy()
for c in range(3):
    rgb_overlay[:, :, c] = np.where(
        low_custom2_mask,
        (1 - alpha) * rgb_overlay[:, :, c] + alpha * overlay_color[c],
        rgb_overlay[:, :, c],
    )

rgb_overlay = rgb_overlay.astype(np.uint8)

plt.figure(figsize=(8, 6))
plt.imshow(rgb_overlay)
plt.title(f"RGB with CUSTOM2 < {threshold} Overlay")
plt.axis("off")
overlay_path = os.path.join(
    folder_path, f"{os.path.splitext(file_name)[0]}_custom2_overlay.png"
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
