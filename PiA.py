from object_detection.object_detection import *
from comms.receive import *
from comms.send import *
from gps.gps import Neo8T
from depth.depth import *
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
def new_scan(rgb_model, activeFile, lon, lat, distance_moved, privacy=False):
    global last_objects
    
    classes = getUserRequestedClasses()

    rgb_model.set_classes(list(classes.keys()))
    
    logging.info(f"Set YOLO classes to {classes}.")
    
    # Captures two images
    setStatusMessage("capturing images")
    frames = capture(cams, "PiA")
    # Triggers capture on PiB
    request_client_capture(server_socket, conn)

    # Sending RGB classes to PiB
    logging.info(f"Sending Object detection classes to PiB.")
    send_object_detection_results(conn, [classes])

    setStatusMessage("detecting objects")
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model, f, OD_THRESHOLD))
    # Retrieve slave images and data
    frames += receive_image_arrays(conn)

    if ENABLE_DEBUG:
        debug_dir = "./debug_PiA/"
        os.makedirs(debug_dir, exist_ok=True)

        for i, frame in enumerate(frames):
            frame_id = len([f for f in os.listdir(debug_dir) if f.endswith(".jpg")])
            cv2.imwrite(os.path.join(debug_dir, f"frame_{frame_id}_{i}.jpg"), frame)

    # # Send object detection results to PiB
    # send_object_detection_results(conn, objects)
    # Receive object detection data
    objects += receive_object_detection_results(conn)

    # Calculate distance estimation to objects - append distance to object array
    # objects = calculate_distance(objects, distance_moved, last_objects)
    last_objects = objects # Update last objects
    # Assign IDs to objects
    objects = assign_id(objects)

    # Blur people if privacy
    setStatusMessage("blurring people")

    # Blur people if privacy
    if privacy:
        for i in range(len(frames)):
            frames[i] = blur_people(frames[i], objects[i], 255)

    setStatusMessage("stitching images")
    # Perform pano stitching
    panorama, objects = performPanoramicStitching(frames, objects)

    # Restructure objects into one array instead of separated by frames
    objects_restructured = []
    for frame in objects:
        objects_restructured += frame

    # Remove duplicate object detections
    setStatusMessage("removing duplicate objects")
    filtered_objects = non_maximum_suppression(objects_restructured)

    # Send filtered objects to PiB
    send_object_detection_results(conn, filtered_objects)

    # Updates json and moves images to correct folder
    setStatusMessage("updating ui")
    uid = str(lon) + str(lat)
    # for i in range(len(filtered_objects)):
    #     filtered_objects[i][1] = xyxy_to_xywh(
    #         filtered_objects[i][1], panorama.shape[1], panorama.shape[0], True
    #     )

    updateJSON(uid, lon, lat, filtered_objects, panorama, activeFile)

    # # Extract filtered IDs
    # filtered_ids = []
    # for obj in filtered_objects:
    #     filtered_ids.append(int(obj[3]))

    # Receive processed hyperspectral scans from PiB
    # Receive hyperspectral material distribution data from PiB
    for i in range(len(filtered_objects)):
        if classes[filtered_objects[i].label]:
            setStatusMessage(f"hyperspectral scanning {filtered_objects[i].label}")
            # Receive scan information
            hs_classification, hs_ndvi = receive_image_arrays(conn)
            hs_materials = receive_object_detection_results(conn)[0]

            id = filtered_objects[i].id
            # Save results to images in ui
            save_path = UI_IMAGES_SAVE_PATH + activeFile[:-5]
            cv2.imwrite(save_path + f"/hs_{uid}_{id}_classification.jpg", hs_classification)
            cv2.imwrite(save_path + f"/hs_{uid}_{id}_ndvi.jpg", hs_ndvi)

            # Update object with refereances and materials
            filtered_objects[i].set_hs_classification_ref(f"./hs_{uid}_{id}_classification.jpg")
            filtered_objects[i].set_hs_ndvi_ref(f"./hs_{uid}_{id}_ndvi.jpg")
            filtered_objects[i].set_hs_materials(hs_materials)

    # Update JSON with hyperspectral data
    updateJSON_HS(filtered_objects, lon, lat, activeFile)


# COMMUNICATIONS
PORT = 5002
HOST = "0.0.0.0"  # i.e. listening

# CAMERA
RESOLUTION = (4608, 2592)
FOV = (102, 67)

# OBJECT DETECTION
PRIVACY = False  # Blur people
CLASSES = ["plant"]
OD_THRESHOLD = 0.1

# UI
UI_IMAGES_SAVE_PATH = "./user-interface/public/images/"

# GPS
GPS_PORT = "/dev/ttyACM0"  # USB Port (check automatically?)
GPS_BAUDRATE = 115200
DISTANCE_THRESHOLD = 10

# Globals
last_objects = []


# OTHER
ENABLE_DEBUG = True

if __name__ == "__main__":
    setStatusMessage("setting up")
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
    # Setup GPS
    gps = Neo8T(
        port=GPS_PORT,
        baudrate=GPS_BAUDRATE,
        timeout=1,
        distance_threshold=DISTANCE_THRESHOLD,
    )
    logging.debug("Setup GPS")
    # Make connection
    server_socket, conn = make_server_connection(HOST, PORT)
    logging.debug("Connected to PiB")
    # Setup object detection model
    rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
    logging.debug("Loaded RGB object detection model.")
    logging.info(f"Privacy set {PRIVACY}.")

    # Make connection
    server_socket, conn = make_server_connection(HOST, PORT)
    logging.debug("Connected to PiB")
    
    logging.info(f"Waiting for trigger...")

    # Mainloop
    while True:
        # Update save location
        try:
            status, activeFile = getPlatformStatus()
        except json.decoder.JSONDecodeError:
            logging.error("Error accessing JSON configuration file.")

        # Update GPS status
        gps_status = gps.check_if_gps_locaiton()
        updateGPSConnection(CONFIGURATION_FILE_PATH, gps_status)

        GPS_coordinate_change = gps.check_for_movement()
        if status == 2 or (status == 1 and GPS_coordinate_change):
            timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            save_location = f"./capture/{timestamp}-capture/"

            # Get current location
            location = gps.get_location()
            distance_moved = gps.get_distance_moved()
            if location:
                    new_scan(
                    rgb_model,
                    activeFile,
                    lat=location["latitude"],
                    lon=location["longitude"], 
                    distance_moved=distance_moved,
                    privacy=PRIVACY,
                )
            else:
                logging.debug("No location => using default Lat and long")
                new_scan(rgb_model, activeFile, privacy=PRIVACY)

            logging.info("Completed scan.")

            if status == 2:
                setPlatformStatus(0)
