from object_detection.object_detection import *
from comms.send import *
from comms.receive import * 
from cameras import *
from time import sleep
import logging
from hyperspectral.zaber_driver import *
from hyperspectral.hyperspectral_driver import *

def on_trigger(rgb_model,axis,hs_cam,cal_arr):
    # Capture images
    frames = capture(cams, "PiB", PATH)
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model,f))
    # Receive object detection data
    detection_data = receive_object_detection_results(client_socket)
    objects = detection_data + objects
    # Send images to PiA
    send_image_arrays(client_socket,frames)
    # Send object detection results to PiA
    send_object_detection_results(client_socket, objects[2:])  
    # TODO: Get objects detected from PiA
    # Take hyperspectral scan - test for 1st object
    px_1 = results[0][0][1][:2]
    px_2 = results[0][0][1][2:]
    angle_x1, _ = pixel_to_angle(px_1,RESOLUTION,FOV)
    angle_x2, _ = pixel_to_angle(px_2,RESOLUTION,FOV)
    on_rotate(axis,(angle_x1,angle_x2),hs_cam,cal_arr)
    # TODO: Send hyperspectral data to PiA
    

def on_rotate(axis,angles,hs_cam,cal_arr):
    # Rotate rotational stage 
    axis.move_relative(angles[0],Units.ANGLE_DEGREES,velocity=40,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True)
    sleep(2)
    logging.info("Rotating hyperspectral to {angles[0]} degrees.")
    # Grab hyperspectral data
    # fps = hs_cam.ResultingFrameRateAbs.Value
    logging.info("Calculated FPS: {fps}")
    rotate_angle = angles[1]-angles[0]
    nframes = 800 #TODO calculate?
    # speed = get_rotation_speed(nframes,fps,rotate_angle)
    logging.info("Grabbing hyperspectral scan...")
    rotate_relative(axis, rotate_angle, 5)
    # scene = grab_avg_hyperspectral_frames(hs_cam, nframes)
    # # Plot RGB image for test
    # print("Plotting RGB Image...")
    # plt.figure()
    # # Get indices of RGB bands from calibration file
    # RGB = (
    #     get_wavelength_index(cal_arr, 690, 2),
    #     get_wavelength_index(cal_arr, 535, 2),
    #     get_wavelength_index(cal_arr, 470, 2),
    # )

    # plt.imshow(scene[:, :, RGB])
    # TODO: Process hs data
    # TODO: return hsi colour image and data


# IP = "10.12.101.192"
IP = "hsiA.local"
PORT = 5002
PATH = "./captures/"
CLASSES = ["person"] 
ROTATIONAL_STAGE_PORT = "/dev/ttyUSB0" # TODO: find automatically?

RESOLUTION = (4608,2592)
FOV = (102,67)

CALIBRATION_FILE_PATH = "./hyperspectral/calibration/BaslerPIA1600_CalibrationA.txt"

if __name__ == "__main__":
    # Setup Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",style="{",datefmt="%Y-%m-%d %H:%M",
        handlers=[
        logging.FileHandler("piB.log"),
        logging.StreamHandler()
        ])
    logging.info("##### Start up new sesson. #####")
    try:
        # Setup cameras and capture images
        cams = setup_cameras()
        logging.debug("Setup cameras.")
        
        # Setup rotational stage
        zaber_conn, axis = setup_zaber(ROTATIONAL_STAGE_PORT)
        logging.debug("Setup rotational stage.")
        
        # Home rotational stage
        axis.home(wait_until_idle=True)
        rotate_relative(axis, 20,40)
        logging.info("Homing rotational stage.")

        # Get Hyperspectral Calibration
        cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)

        # Setup hyperspectral
        # hs_cam = setup_hyperspectral()
        # logging.info("Setup hyperspectral camera.")
        hs_cam = None

        # Make connection with PiA
        client_socket = make_client_connection(IP, PORT)
        logging.debug("Connected to PiA")
        
        # Setup object detection model
        rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
        logging.debug("Loaded RGB object detection model.")
        # TODO send search classes to PiB
        rgb_model.set_classes(CLASSES)
        logging.info(f"Set YOLO classes to {CLASSES}.")
        logging.info(f"Waiting for trigger...")

        # Poll for trigger capture signal
        while True:
            if receive_capture_request(client_socket) == 1:
                logging.info("Triggered Capture.")
                on_trigger(rgb_model,axis,hs_cam,cal_arr)
                capture_triggered = True
            
            sleep(1)
    
    except Exception as e:
        logging.error(f"Error in PiB.py: {e}")
        client_socket.close()
        hs_cam.Close()
        zaber_conn.close()
        logging.info("All connections closed.")

    finally:
        client_socket.close()
        zaber_conn.close()
    

