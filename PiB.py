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

def on_trigger(rgb_model,axis,hs_cam,cal_arr):
    # Capture images
    frames = capture(cams, "PiB", PATH)
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model,f))
    # Send images to PiA
    send_image_arrays(client_socket,frames)
    # Receive object detection data
    detection_data = receive_object_detection_results(client_socket)
    objects = detection_data + objects
    # Send object detection results to PiA
    send_object_detection_results(client_socket, objects[2:])  
    # Assign IDs to objects
    objects = assign_id(objects)

    # Take hyperspectral scan 
    hs_materials = []
    for i in range(len(objects)):# For every camera
        if objects[i] != None:
            for j in range(len(objects[i])):# for every object detected in frame
                # Get corner pixels of objects detected and convert to angle
                px_1,px_2 = objects[i][j][1][:2],objects[i][j][1][2:]
                xoffset = i*90
                angle_x1 = pixel_to_angle(px_1,RESOLUTION,FOV)[0] + xoffset + ROTATION_OFFSET 
                angle_x2 = pixel_to_angle(px_2,RESOLUTION,FOV)[0] + xoffset + ROTATION_OFFSET
                id = objects[i][j][3]
                logging.debug(f"Camera {i}, object {j}, ID: {id}, X pixel coords: {px_1},{px_2} => X angle: {angle_x1},{angle_x2}")

                if ENABLE_HS:
                    mats = on_rotate(axis,(angle_x1,angle_x2),hs_cam,cal_arr, id)
                    hs_materials.append(mats)
                    
    # Send processed hyperspectral scans to PiA
    send_images(client_socket, HSI_SCANS_PATH)            
    # Send hyperspectral material distribution data to PiA
    send_object_detection_results(client_socket, hs_materials)
    # Remove all old hs scans
    delete_files_in_dir(HSI_SCANS_PATH)
    
                

def on_rotate(axis,angles,hs_cam,cal_arr, id):
    # Rotate rotational stage 
    axis.move_absolute(angles[0],Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True)
    logging.info(f"Rotating hyperspectral to {angles[0]} degrees.")
    # Grab hyperspectral data
    fps = hs_cam.ResultingFrameRateAbs.Value
    logging.debug(f"Calculated FPS: {fps}")
    # Calculate number of frames
    nframes = get_nframes(abs(angles[1]-angles[0]))
    logging.debug(f"Will grab {nframes} frames.")
    speed = get_rotation_speed(nframes,fps,abs(angles[1]-angles[0]))
    logging.info("Grabbing hyperspectral scan...")
    axis.move_absolute(angles[1],Units.ANGLE_DEGREES,velocity=speed,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=False) # temporarily blocking
    scene = grab_hyperspectral_scene(hs_cam, nframes, None, None,"test",calibrate=False)
    # Plot RGB image for test
    # print("Plotting RGB Image...")
    # plt.figure()
    # Get indices of RGB bands from calibration file
    # RGB = (
    #     get_wavelength_index(cal_arr, 690, 2),
    #     get_wavelength_index(cal_arr, 535, 2),
    #     get_wavelength_index(cal_arr, 470, 2),
    # )

    # plt.imshow(scene[:, :, RGB])
    output_path = HSI_SCANS_PATH+f"hs_{id}.jpg"
    mats = classify_and_save(MODEL_PATH, scene, LABEL_ENCODING_PATH, output_path)
    print(mats)

    return mats




# IP = "hsiA.local"

ENABLE_HS = False

IP = "10.42.0.1"
PORT = 5002
PATH = "./captures/"
CLASSES = ["person"] 
ROTATIONAL_STAGE_PORT = "/dev/ttyUSB0" # TODO: find automatically?
ROTATION_OFFSET = 20  # temporary 

RESOLUTION = (4608,2592)
FOV = (102,67)

CALIBRATION_FILE_PATH = "./hyperspectral/calibration/BaslerPIA1600_CalibrationA.txt"


MODEL_PATH = "./hyperspectral/NN_18_03_2025.keras"
LABEL_ENCODING_PATH = "./hyperspectral/label_encoding.npy"
HSI_SCANS_PATH = "./hsi_scans/"

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
        
        
        
        if ENABLE_HS:
            # Setup rotational stage
            zaber_conn, axis = setup_zaber(ROTATIONAL_STAGE_PORT)
            logging.debug("Setup rotational stage.")
    
            # Home rotational stage
            logging.info("Homing rotational stage.")
            axis.home(wait_until_idle=True)
            axis.move_absolute(ROTATION_OFFSET,Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True) # temporarily blocking

            # Setup hyperspectral
            hs_cam = setup_hyperspectral()
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
        # TODO send search classes to PiB
        rgb_model.set_classes(CLASSES)
        logging.info(f"Set YOLO classes to {CLASSES}.")
        
        logging.info("Setup complete. Waiting to start capture...")

        # Poll for trigger capture signal
        while True:
            if receive_capture_request(client_socket) == 1:
                logging.info("Triggered Capture.")
                on_trigger(rgb_model,axis,hs_cam,cal_arr)
                capture_triggered = True
            
            sleep(1)
    
    except Exception as e:
        logging.error(f"Error in PiB.py: {e}")

        if ENABLE_HS:
            axis.move_absolute(2,Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True) # temporarily blocking
            hs_cam.Close()
            zaber_conn.close()
        client_socket.close()
        logging.info("All connections closed.")

    finally:
        if ENABLE_HS:
            axis.move_absolute(2,Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True) # temporarily blocking
            hs_cam.Close()
            zaber_conn.close()
        client_socket.close()
        logging.info("All connections closed.")
        logging.info("System terminated.")
    


