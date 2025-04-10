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
import traceback


# Triggers when change in GPS location
def new_scan(
    rgb_model, activeFile, lat, lon, time, distance_moved, manual_hs, privacy=False
):
    global last_objects

    # Update classes of objects to detect from UI
    classes = getUserRequestedClasses()

    # If privacy enabled and "person" class not included,
    # it is added to allow blurring
    if privacy:
        if "person" not in list(classes.keys()):
            classes["person"] = False

    # Update YOLO model with objects of interest
    logging.info(f"Set objects of interest to {list(classes.keys())}.")
    rgb_model.set_classes(list(classes.keys()))

    # Captures two images
    setStatusMessage("capturing images")
    frames = capture(cams, "PiA")

    # Triggers capture on PiB
    request_client_capture(server_socket, conn)

    # Wait for PiB to have captured
    capture_success = False
    while not capture_success:
        capture_success = check_capture_success(conn)

    # Sending RGB classes to PiB
    logging.info("Sending Object detection classes to PiB.")
    send_object_detection_results(conn, [classes])

    setStatusMessage("detecting objects")
    # Perform object detection
    objects = []
    for i, f in enumerate(frames):
        objects.append(object_detection(rgb_model, f, i, OD_THRESHOLD))

    # Retrieve slave images and data
    logging.info("Receiving PiB frames")
    frames += receive_image_arrays(conn)

    # If in debug mode, save rgb frames
    if ENABLE_DEBUG:
        debug_dir = "./debug_PiA/"
        os.makedirs(debug_dir, exist_ok=True)

        for i, frame in enumerate(frames):
            frame_id = len([f for f in os.listdir(debug_dir) if f.endswith(".jpg")])
            path = os.path.join(debug_dir, f"frame_{frame_id}_{i}.jpg")
            cv2.imwrite(path, frame)

        logging.debug(f"Saved individual RGB frames to {path}")

    # # Send object detection results to PiB
    # send_object_detection_results(conn, objects)
    # Receive object detection data
    objects += receive_object_detection_results(conn)

    # Calculate distance estimation to objects - append distance to object array
    # objects = calculate_distance(objects, distance_moved, last_objects)
    last_objects = objects  # Update last objects
    # Assign IDs to objects
    objects = assign_id(objects)

    # Send manual hyperspectral options
    logging.debug("Send manual hyperspectral scan option value")
    send_object_detection_results(conn, [manual_hs])

    # Blur people if privacy
    setStatusMessage("blurring people")
    if privacy:
        for i in range(len(frames)):
            frames[i] = blur_people(frames[i], objects[i], 255)

    setStatusMessage("stitching images")
    # Perform pano stitching
    panorama, objects = performPanoramicStitching(frames, objects)

    # Restructure objects into one array instead of separated by frames
    logging.debug("Restructuring objects array")
    objects_restructured = []
    for frame in objects:
        objects_restructured += frame

    # Remove duplicate object detections
    setStatusMessage("removing duplicate objects")
    filtered_objects = non_maximum_suppression(objects_restructured)

    # Updates json and moves images to correct folder
    setStatusMessage("updating ui")
    # uid = str(lon) + str(lat)
    uid = f"{lat},{lon}-{time.strftime("%Y%m%d_%H%M%S")}"
    updateJSON(uid, lat, lon, filtered_objects, panorama, activeFile)

    # If manual hs scan checked
    if manual_hs:
        # Perform singular 360 hs scan
        logging.debug("Recieving manual hyperspectral scan results")
        setStatusMessage("Performing manual 360 hyperspectral scan")
        hs_classification, hs_ndvi, hs_pi, hs_rgb = receive_image_arrays(conn)
        hs_materials = receive_object_detection_results(conn)[0]

        # Save results to images in ui
        id = -1

        # Save paths
        save_path = UI_IMAGES_SAVE_PATH + activeFile[:-5]
        hsi_ref = f"/hs_{uid}_{id}_classification.jpg"
        ndvi_ref = f"/hs_{uid}_{id}_ndvi.jpg"
        pi_ref = f"/hs_{uid}_{id}_pi.jpg"
        rgb_ref = f"/hs_{uid}_{id}_rgb.jpg"

        logging.debug(f"Writing images to {save_path}")
        cv2.imwrite(save_path + hsi_ref, hs_classification)
        cv2.imwrite(save_path + ndvi_ref, hs_ndvi)
        cv2.imwrite(save_path + pi_ref, hs_pi)
        cv2.imwrite(rgb_ref, hs_rgb)

        # Update JSON with hyperspectral data
        updateJSON_HS(
            filtered_objects,
            lat,
            lon,
            activeFile,
            hsi_ref,
            ndvi_ref,
            pi_ref,
            hs_materials,
            rgb_ref,
        )
    else:
        # Send filtered objects to PiB
        logging.debug(
            "Sending filtered object detection results to PiB for hyperspectral scanning"
        )
        send_object_detection_results(conn, filtered_objects)

        # Receive processed hyperspectral data from PiB for each object
        for i in range(len(filtered_objects)):
            if classes[filtered_objects[i].label]:
                setStatusMessage(f"hyperspectral scanning {filtered_objects[i].label}")
                logging.debug(f"hyperspectral scanning {filtered_objects[i].label}")

                # Receive scan information
                logging.debug(f"Receiving scan data")
                hs_classification, hs_ndvi, hs_pi, hs_rgb = receive_image_arrays(conn)
                hs_materials = receive_object_detection_results(conn)[0]
                logging.debug("Received scan data")

                id = filtered_objects[i].id
                save_path = UI_IMAGES_SAVE_PATH + activeFile[:-5]
                hsi_ref = f"/hs_{uid}_{id}_classification.jpg"
                ndvi_ref = f"/hs_{uid}_{id}_ndvi.jpg"
                pi_ref = f"/hs_{uid}_{id}_pi.jpg"
                rgb_ref = f"/hs_{uid}_{id}_rgb.jpg"

                # Save results to images in ui
                logging.debug(f"Writing images to {save_path}")
                cv2.imwrite(save_path + hsi_ref, hs_classification)
                cv2.imwrite(save_path + ndvi_ref, hs_ndvi)
                cv2.imwrite(save_path + pi_ref, hs_pi)
                cv2.imwrite(save_path + rgb_ref, hs_rgb)

                # Update object with refereances and materials
                filtered_objects[i].set_hs_classification_ref(hsi_ref)
                filtered_objects[i].set_hs_ndvi_ref(ndvi_ref)
                filtered_objects[i].set_hs_pi_ref(pi_ref)
                filtered_objects[i].set_hs_rgb_ref(rgb_ref)
                filtered_objects[i].set_hs_materials(hs_materials)

        # Update JSON with hyperspectral data
        updateJSON_HS(
            filtered_objects,
            lat,
            lon,
            activeFile,
        )


# ----- GLOBAL VARIABLES ----- #

# COMMUNICATIONS
PORT = 5002
HOST = "0.0.0.0"  # i.e. listening

# CAMERA
RESOLUTION = (4608, 2592)
FOV = (102, 67)

# OBJECT DETECTION
PRIVACY = True  # Blur people
CLASSES = ["person"]
OD_THRESHOLD = 0.03
last_objects = []

# UI
UI_IMAGES_SAVE_PATH = "./user-interface/public/images/"

# GPS
GPS_PORT = "/dev/ttyACM0"
GPS_BAUDRATE = 115200
DISTANCE_THRESHOLD = 10

# OTHER
ENABLE_DEBUG = True

# ----- MAIN ----- #
if __name__ == "__main__":
    # Update UI status msg
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

    try:
        # Setup cameras and GPIO
        cams = setup_cameras()
        logging.debug(f"Setup {len(cams)} cameras.")
        if len(cams) < 2:
            raise Exception(
                "Cameras not working. Check connections."
            )  # TODO move into function

        # Setup GPS
        gps = Neo8T(
            port=GPS_PORT,
            baudrate=GPS_BAUDRATE,
            timeout=1,
            distance_threshold=DISTANCE_THRESHOLD,
        )
        logging.debug("Setup GPS")

        # Make connection to PiB
        server_socket, conn = make_server_connection(HOST, PORT)
        logging.debug("Connected to PiB")

        # Setup object detection model
        rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
        logging.debug("Loaded RGB object detection model.")

        logging.info("All systems setup.")
        logging.info(f"Privacy set {PRIVACY}.")
        logging.info(f"Waiting for trigger from UI...")

        setStatusMessage("setup complete. ready for capture")

        ### Mainloop ###
        count = 0
        while True:
            # Update save location
            status = None
            while not status:
                try:
                    status, activeFile, hsi_manual = getPlatformStatus()
                except json.decoder.JSONDecodeError:
                    logging.error("Error accessing JSON configuration file.")
                sleep(0.25)

            # Update GPS location and check for change in location > than  DISTANCE_THRESHOLD
            GPS_coordinate_change = gps.check_for_movement()
            if GPS_coordinate_change:
                logging.info("Movement detected.")

            # If manual UI trigger or in wait for movement mode + change in movement, perform new scn
            if status == 2 or (status == 1 and GPS_coordinate_change):
                logging.info("Scan triggered.")

                # Get current location
                location = gps.get_location()
                distance_moved = gps.get_distance_moved()
                logging.info(f"Location: {location}")
                logging.info(f"Distance moved: {distance_moved}m")

                # If location known, trigger a new scan
                if location:
                    new_scan(
                        rgb_model,
                        activeFile,
                        lat=location["latitude"],
                        lon=location["longitude"],
                        time=datetime.now(),
                        distance_moved=distance_moved,
                        manual_hs=hsi_manual,
                        privacy=PRIVACY,
                    )
                else:
                    logging.info("No GPS location found. Try again.")
                    setPlatformStatus(0)

                logging.info("Completed scan.")

                if status == 2:
                    setPlatformStatus(0)

            # Update GPS status every 30 cycles
            if count > 50:
                gps.update_location()
                gps_status = gps.check_if_gps_locaiton()
                updateGPSConnection(CONFIGURATION_FILE_PATH, gps_status)

            count += 1

    except KeyboardInterrupt:
        logging.error(f"Keyboard interrupt")
        server_socket.close()
        logging.info("All connections closed.")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line, func, text = tb[-1]
        logging.critical(f"Error in PiB.py: {e}")
        logging.critical(f"Occurred in file:{filename}, line {line}")

        server_socket.close()
        logging.info("All connections closed.")

    finally:
        setPlatformStatus(0)
        logging.info("System terminated.")
