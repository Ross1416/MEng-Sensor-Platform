from object_detection.object_detection import *
from comms.receive import *
from comms.send import *
from datetime import datetime
from time import sleep
from comms.updateJSON import *
import cv2
from cameras import *
import logging
from stitching.stitching_main import performPanoramicStitching
import json
import shutil


# Triggers when change in GPS location
def new_scan(rgb_model, activeFile, lon=55.3, lat=-4, privacy=False):
    # Captures two images
    frames = capture(cams, "PiA")
    # Triggers capture on PiB
    request_client_capture(server_socket, conn)
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model, f))
    # Retrieve slave images and data
    frames += receive_image_arrays(conn)

    if ENABLE_DEBUG:
        debug_dir = "./debug_PiA/"
        os.makedirs(debug_dir, exist_ok=True)

        for i, frame in enumerate(frames):
            frame_id = len(
                [f for f in os.listdir(debug_dir) if f.endswith(".jpg")]
            )
            cv2.imwrite(
                os.path.join(debug_dir, f"frame_{frame_id}.jpg"), frame
            )

    # Send object detection results to PiB
    send_object_detection_results(conn, objects)
    # Receive object detection data
    objects += receive_object_detection_results(conn)
    # Assign IDs to objects
    objects = assign_id(objects)

    # Blur people if privacy
    if privacy:
        for i in range(len(frames)):
            frames[i] = blur_people(frames[i], objects[i], 255)

    # Perform pano stitching
    panorama, objects = performPanoramicStitching(frames, objects)
    # Restructure objects
    objects_restructured = []
    for frame in objects:
        objects_restructured += frame

    # Remove duplicate object detections
    filtered_objects = non_maximum_suppression(objects_restructured)

    # Updates json and moves images to correct folder
    uid = str(lon) + str(lat)
    for i in range(len(filtered_objects)):
        filtered_objects[i][1] = xyxy_to_xywh(
            filtered_objects[i][1], panorama.shape[1], panorama.shape[0], True
        )

    updateJSON(uid, lon, lat, filtered_objects, panorama, activeFile)

    # Receive processed hyperspectral scans from PiB
    # Receive hyperspectral material distribution data from PiB
    hs_materials = []
    for i in range(len(objects_restructured)):
        receive_images(conn, HSI_SCANS_PATH)
        mats = receive_object_detection_results(conn)
        hs_materials.append(mats)

    # Extract filtered IDs
    ids = filtered_objects[:][0]

    # Remove unneeded hs_materals where objects are removed with NMS
    filtered_hs_materials = []
    for i in range(len(hs_materials)):
        if i in ids:
            filtered_hs_materials.append(hs_materials)

    # Rename with lat, lon and move to correct location
    hs_classification = []
    hs_ndvi = []
    files = os.listdir(HSI_SCANS_PATH)
    for scan in files:
        path = os.path.join(path, scan)
        if os.path.isfile(path) and scan.endswith(".png"):
            loc = scan.find("_") + 1
            id = scan[loc : loc + 2]
            # Check if id of hyperspectral scan is in filtered objects
            if id in ids:
                if "ndvi" in path:
                    save_path = f"./user-interface/public/images/{activeFile[:-5]}/{uid}/hs_{uid}_{id}.jpg"
                    shutil.move(path, save_path)
                    hs_classification.append(f"./{uid}/hs_{uid}_{id}.jpg")
                else:
                    save_path = f"./user-interface/public/images/{activeFile[:-5]}/{uid}/hs_{uid}_{id}_ndvi.jpg"
                    shutil.move(path, save_path)
                    hs_ndvi.append(f"./{uid}/hs_{uid}_{id}_ndvi.jpg")

    # Remove all unmoved (unnecessary HS scans)
    delete_files_in_dir(HSI_SCANS_PATH)

    # Update JSON with hyperspectral data
    updateJSON_HS(
        hs_classification, hs_ndvi, hs_materials, lon, lat, activeFile
    )


PORT = 5002
HOST = "0.0.0.0"  # i.e. listening
RESOLUTION = (4608, 2592)
FOV = (102, 67)
PRIVACY = True  # Blur people
CLASSES = ["person"]

ENABLE_DEBUG = False

HSI_SCANS_PATH = "./hsi_scans/"

if __name__ == "__main__":
    # Setup Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        handlers=[logging.FileHandler("piA.log"), logging.StreamHandler()],
    )
    logging.info("##### Start up new sesson. #####")
    # Setup cameras and GPIO
    cams = setup_cameras()
    logging.debug("Setup cameras.")
    # Make connection
    server_socket, conn = make_server_connection(HOST, PORT)
    logging.debug("Connected to PiB")
    # Setup object detection model
    rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
    logging.debug("Loaded RGB object detection model.")
    rgb_model.set_classes(CLASSES)
    logging.info(f"Set YOLO classes to {CLASSES}.")
    logging.info(f"Privacy set {PRIVACY}.")
    logging.info(f"Waiting for trigger...")

    # Mainloop
    while True:
        # TODO: Check for location change
        # Update save location
        try:
            status, activeFile = getPlatformStatus()
        except json.decoder.JSONDecodeError:
            logging.error("Error accessing JSON configuration file.")
        GPS_coordinate_change = True

        if status == 2 or (status == 1 and GPS_coordinate_change):
            timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            save_location = f"./capture/{timestamp}-capture/"

            new_scan(rgb_model, activeFile, privacy=PRIVACY)

            logging.info("Completed scan.")

            if status == 2:
                setPlatformStatus(0)
