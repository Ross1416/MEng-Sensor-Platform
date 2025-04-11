from object_detection.object_detection import *
from comms.send import *
from comms.receive import *
from cameras import *
from time import sleep
import logging
from hyperspectral.zaber_driver import *
from hyperspectral.hyperspectral_driver import *
from hyperspectral.classification import *
import time
import traceback


def on_trigger(rgb_model, axis, hs_cam, cal_arr):
    # Capture images
    frames = capture(cams, "PiB")

    # Send capture success to PiA
    send_capture_success(client_socket)

    # Receive object detection classes from PiA
    logging.debug("Receiving object detection classes from PiA")
    classes = receive_object_detection_results(client_socket)[0]
    classes_list = list(classes.keys())
    if classes_list != []:
        rgb_model.set_classes(classes_list)

    logging.debug("Successfully received object detection classes from PiA")
    logging.info(f"Set RGB object detection classes to {classes_list}.")

    # Perform object detection
    objects = []
    for i, f in enumerate(frames):
        objects.append(object_detection(rgb_model, f, i + 2, OD_THRESHOLD))

    # Send images to PiA
    logging.debug("Sending RGB image frames to PiA")
    send_image_arrays(client_socket, frames)

    # # Receive object detection data
    # detection_data = receive_object_detection_results(client_socket)
    # objects = detection_data + objects
    # Send object detection results to PiA
    # send_object_detection_results(client_socket, objects[2:])

    logging.debug("Sending object detection results to PiA")
    send_object_detection_results(client_socket, objects)

    # # Assign IDs to objects
    # objects = assign_id(objects)

    # Receive hyperspectral manual scan toggle
    logging.debug("Receiving hyperspectral manual toggle option from PiA")
    manual_hs = receive_object_detection_results(client_socket)[0]

    if manual_hs:
        # Perform full 360 degree scan
        if ENABLE_HS:
            logging.debug("Performing manual hyperspectral scan")
            mats, hs_classification, hs_ndvi, hs_msavi, hs_custom2, hs_artificial, hs_rgb = on_rotate(
                axis, (-110, 110), hs_cam, cal_arr, -1, True
            )
            logging.debug("Sending manual hyperspectral scan results to PiA")
            send_image_arrays(
                client_socket, [hs_classification, hs_ndvi, hs_msavi, hs_custom2, hs_artificial, hs_rgb]
            )
            send_object_detection_results(client_socket, [mats])
            logging.debug("Successfully sent manual hyperspectral scan results to PiA")
    else:
        # Scan individual objects
        # Receive filtered objects
        logging.debug("Scanning objects of interest")
        logging.debug("Receiving filtered object detection results")
        objects = receive_object_detection_results(client_socket)

        # Take hyperspectral scan
        for i in range(len(objects)):  # for every object detected in frame
            logging.debug(f"Transforming object {i} co-ordinates to rotation angles")
            # Get corner pixels of objects detected and convert to angle
            px_1 = objects[i].get_xyxy_original()[:2]
            px_2 = objects[i].get_xyxy_original()[2:]
            xoffset = objects[i].get_camera() * 90
            angle_x1 = (
                pixel_to_angle(px_1, RESOLUTION, FOV)[0] + xoffset  # + ROTATION_OFFSET
            )
            angle_x2 = (
                pixel_to_angle(px_2, RESOLUTION, FOV)[0] + xoffset  # + ROTATION_OFFSET
            )

            if ENABLE_HS:
                # Check if object should be scanned by hyperspectral
                if classes[objects[i].label]:
                    id = objects[i].id
                    logging.debug(
                        f"Scanning Object {i}, ID: {id}, X pixel coords: {px_1},{px_2} => X angle: {angle_x1},{angle_x2}"
                    )
                    mats, hs_classification, hs_ndvi, hs_msavi, hs_custom2, hs_artificial, hs_rgb = on_rotate(
                        axis, (angle_x1, angle_x2), hs_cam, cal_arr, id, False
                    )
                    logging.debug("Sending scan results to PiA")
                    send_image_arrays(
                        client_socket, [hs_classification, hs_ndvi, hs_msavi, hs_custom2, hs_artificial, hs_rgb]
                    )
                    send_object_detection_results(client_socket, [mats])


def on_rotate(axis, angles, hs_cam, cal_arr, id, manual_hs=False):

    # Grab hyperspectral data
    fps = hs_cam.ResultingFrameRateAbs.Value
    logging.debug(f"Calculated FPS: {fps}")

    # Calculate difference in angle and set minimum of 27 degrees
    diff = abs(angles[1] - angles[0])
    if diff < HS_MIN_CAPTURE_ANGLE:
        extra = int((HS_MIN_CAPTURE_ANGLE - diff) / 2)
        angles = (angles[0] - extra, angles[1] + extra)
    diff = abs(angles[1] - angles[0])
    logging.debug(f"Scan angles {angles[0]} to {angles[1]}")

    # Rotate rotational stage
    rotate_safe(axis, angles[0], ROTATION_OFFSET, ROTATION_SPEED, blocking=True)

    # Calculate number of frames
    nframes = get_nframes(diff, HS_PIXEL_BINNING)
    logging.debug(f"Will grab {nframes} frames.")
    speed = get_rotation_speed(nframes, fps, diff)
    logging.info("Grabbing hyperspectral scan...")
    rotate_safe(axis, angles[1], ROTATION_OFFSET, speed, blocking=False)
    scene = grab_hyperspectral_scene(
        hs_cam, nframes, None, None, "test", calibrate=False
    )

    # Save scene as .npy if debugging
    if ENABLE_DEBUG:
        logging.debug("Saving debug data")
        # debug_dir = "./debug_PiB/"
        debug_dir = "/media/groupc/44A2-2862/debug_PiB/"  # USB debug path
        os.makedirs(debug_dir, exist_ok=True)
        next_id = len(
            [
                f
                for f in os.listdir(debug_dir)
                if f.startswith("scene_") and f.endswith(".npy")
            ]
        )
        path = os.path.join(debug_dir, f"scene_{next_id}.npy")
        np.save(path, scene)
        logging.debug(f"Saved raw hyperspectral scene to {path}")

    # Save RGB image
    logging.debug("Saving HS RGB image")
    RGB = (
        get_wavelength_index(cal_arr, 690, 2),
        get_wavelength_index(cal_arr, 535, 2),
        get_wavelength_index(cal_arr, 470, 2),
    )

    rgb_image = scene[:, :, RGB]
    plt.imsave(HSI_SCANS_PATH + f"hs_{id}_rgb.png", rgb_image)

    output_path = HSI_SCANS_PATH + f"hs_{id}.png"
    mats = classify_and_save(
        MODEL_PATH, scene, LABEL_ENCODING_PATH, output_path, cal_arr
    )

    # Open plots as arrays
    logging.debug("Reading HS image results")
    hs_rgb = cv2.imread(HSI_SCANS_PATH + f"hs_{id}_rgb.png")
    hs_classification = cv2.imread(HSI_SCANS_PATH + f"hs_{id}_classification.png")
    hs_ndvi = cv2.imread(HSI_SCANS_PATH + f"hs_{id}_ndvi.png")
    hs_msavi = cv2.imread(HSI_SCANS_PATH + f"hs_{id}_msavi.png")
    hs_custom2 = cv2.imread(HSI_SCANS_PATH + f"hs_{id}_custom2.png")
    hs_artificial = cv2.imread(HSI_SCANS_PATH + f"hs_{id}_artificial.png")

    return mats, hs_classification, hs_ndvi, hs_msavi, hs_custom2, hs_artificial, hs_rgb


# ----- GLOBAL VARIABLES ----- #

# COMMUNICATIONS
IP = "10.42.0.1"
PORT = 5002

# CAMERA
RESOLUTION = (4608, 2592)
FOV = (102, 67)

# OBJECT DETECTION
CLASSES = ["person"]
OD_THRESHOLD = 0.1

# HYPERSPECTRAL
MODEL_PATH = "./hyperspectral/NN_18_03_2025.keras"
LABEL_ENCODING_PATH = "./hyperspectral/label_encoding.npy"
CALIBRATION_FILE_PATH = "./hyperspectral/calibration/BaslerPIA1600_CalibrationA.txt"
HSI_SCANS_PATH = "./hsi_scans/"
HS_EXPOSURE_TIME = 10000
HS_PIXEL_BINNING = 2
HS_GAIN = 200
HS_MIN_CAPTURE_ANGLE = 27

ROTATIONAL_STAGE_PORT = "/dev/ttyUSB0"
ROTATION_OFFSET = -8
ROTATION_SPEED = 50

# OTHER
ENABLE_HS = True
ENABLE_DEBUG = True

# ----- MAIN ----- #
if __name__ == "__main__":

    # Setup Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        handlers=[logging.FileHandler("piB.log"), logging.StreamHandler()],
    )
    logging.info("##### Start up new sesson. #####")

    try:
        # Setup cameras and capture images
        cams = setup_cameras()
        logging.debug(f"Setup {len(cams)} cameras.")
        if len(cams) < 2:
            raise Exception(
                "Cameras not working. Check connections."
            )  # TODO move into function

        if ENABLE_HS:  # Debug option for testing
            # Setup rotational stage
            zaber_conn, axis = setup_zaber(ROTATIONAL_STAGE_PORT)
            logging.debug("Setup rotational stage.")

            # Home rotational stage
            logging.info("Homing rotational stage.")
            axis.home(wait_until_idle=True)
            rotate_safe(axis, 0, ROTATION_OFFSET, ROTATION_SPEED, blocking=True)

            # Setup hyperspectral
            hs_cam = setup_hyperspectral(HS_EXPOSURE_TIME, HS_GAIN, HS_PIXEL_BINNING)
            logging.info("Setup hyperspectral camera.")

        else:
            axis = None
            hs_cam = None

        # Get Hyperspectral Calibration
        cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)

        # Make connection with PiA
        client_socket = make_client_connection(IP, PORT)
        logging.debug("Connected to PiA")

        # Setup object detection modelx
        rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
        logging.debug("Loaded RGB object detection model.")
        rgb_model.set_classes(CLASSES)
        logging.info(f"Set YOLO classes provisionally to {CLASSES}.")

        # Perform final setup rotation
        rotate_safe(axis, 170, ROTATION_OFFSET, ROTATION_SPEED, blocking=True)

        logging.info("Setup complete. Waiting to start capture...")

        # Poll for trigger capture signal
        while True:
            if receive_capture_request(client_socket) == 1:
                logging.info("Triggered Capture.")
                on_trigger(rgb_model, axis, hs_cam, cal_arr)
                rotate_safe(axis, 170, ROTATION_OFFSET, ROTATION_SPEED, blocking=True)
                capture_triggered = True
            sleep(1)

    except KeyboardInterrupt:
        logging.error(f"Keyboard interrupt")

        if ENABLE_HS:
            rotate_safe(axis, 2, 0, ROTATION_SPEED, blocking=True)
            hs_cam.Close()
            zaber_conn.close()
        client_socket.close()
        logging.info("All connections closed.")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line, func, text = tb[-1]
        logging.critical(f"Error in PiB.py: {e}")
        logging.critical(f"Occurred in file:{filename}, line {line}")

        if ENABLE_HS:
            rotate_safe(axis, 2, 0, ROTATION_SPEED, blocking=True)
            hs_cam.Close()
            zaber_conn.close()
        client_socket.close()
        logging.info("All connections closed.")

    finally:
        logging.info("System terminated.")
