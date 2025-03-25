from object_detection.object_detection import *
from comms.comms_oop import *
from cameras import *
from time import sleep
import logging
import queue
from hyperspectral.zaber_driver import *
from hyperspectral.hyperspectral_driver import *

# REMOTE_HOST = "10.42.0.1"
REMOTE_HOST = "192.168.1.211"

def on_trigger(rgb_model,axis,hs_cam,cal_arr,commsHandler):
    # Capture images
    frames = capture(cams, "PiB", PATH)
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model,f))
    # Send images to PiA
    compressed_frames = []
    for img in frames:
        success, encoded_img = cv2.imencode('.jpg', img)
        if success:
            compressed_frames.append(encoded_img.tobytes())
        else:
            logging.error("Failed to compress frame")
    
    logging.info(f"Sending {len(compressed_frames)} compressed frames")
    commsHandler.send_image_frames(compressed_frames)

    logging.info("Sending object detection data to Parent.")
    # Send object detection results to PiA
    commsHandler.send_object_detection_results(objects)  

    # Take hyperspectral scan 
    for i in range(len(objects)):# For every camera
        if objects[i] != None:
            for j in range(len(objects[i])):# for every object detected in frame
                # Get corner pixels of objects detected and convert to angle
                px_1,px_2 = objects[i][j][1][:2],objects[i][j][1][2:]
                xoffset = i*90
                angle_x1 = pixel_to_angle(px_1,RESOLUTION,FOV)[0] + xoffset + ROTATION_OFFSET # To remove rotation offset 
                angle_x2 = pixel_to_angle(px_2,RESOLUTION,FOV)[0] + xoffset + ROTATION_OFFSET

                logging.debug(f"Camera {i}, object {j}: X pixel coords: {px_1},{px_2} => X angle: {angle_x1},{angle_x2}")

                if ENABLE_HS:
                    on_rotate(axis,(angle_x1,angle_x2),hs_cam,cal_arr)
                # TODO: Send hyperspectral data to PiA

    return objects
        

def on_rotate(axis,angles,hs_cam,cal_arr):
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
    print("Plotting RGB Image...")
    plt.figure()
    # Get indices of RGB bands from calibration file
    RGB = (
        get_wavelength_index(cal_arr, 690, 2),
        get_wavelength_index(cal_arr, 535, 2),
        get_wavelength_index(cal_arr, 470, 2),
    )

    plt.imshow(scene[:, :, RGB])
    # TODO: Process hs data
    # TODO: return hsi colour image and data


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

received_objects = []
# Usage in PiB (child)
def child_message_handler(message_type, payload):
    """Handle messages in child (PiB)"""
    global received_objects

    match message_type:
        case MessageType.CONNECT:
            logging.info("Connected to parent")
            return True
        case MessageType.DISCONNECT:
            logging.info("Parent disconnected")
            return True
        case MessageType.HEARTBEAT:
            # Just acknowledge heartbeat
            return True
        case MessageType.CAPTURE_REQUEST:
            logging.info("Capture request received")
            # Trigger capture sequence
            logging.info("Triggered Capture.")
            on_trigger(rgb_model,axis,hs_cam,cal_arr,commsHandlerInstance)
            # capture_triggered = True
            return True
        case MessageType.OBJECT_DETECTION:
            received_objects = payload
            logging.info(f"Received object detection data from parent")
            # Process objects
            return True
        case MessageType.ERROR:
            logging.error(f"Communication error: {payload}")
            return True
        case _:
            return False

if __name__ == "__main__":
    # Setup Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        handlers=[
            logging.FileHandler("piB.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("PiB")
    logging.info("##### Start up new sesson. #####")

    # Setup comms handler instance
    commsHandlerInstance = CommsHandler(is_parent=False, host=HOST, port=PORT, remote_host=REMOTE_HOST)
    commsHandlerInstance.start()

    try:
        # Setup cameras and capture images
        cams = setup_cameras()
        logger.debug("Setup cameras.")
        
        
        if ENABLE_HS:
            # Setup rotational stage
            zaber_conn, axis = setup_zaber(ROTATIONAL_STAGE_PORT)
            logger.debug("Setup rotational stage.")
    
            # Home rotational stage
            logger.info("Homing rotational stage.")
            axis.home(wait_until_idle=True)
            axis.move_absolute(ROTATION_OFFSET,Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True) # temporarily blocking

            # Setup hyperspectral
            hs_cam = setup_hyperspectral()
            logger.info("Setup hyperspectral camera.")

        else:
            axis = None
            hs_cam = None
        # Get Hyperspectral Calibration
        cal_arr = get_calibration_array(CALIBRATION_FILE_PATH)


        # Setup object detection modelx
        rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
        logger.debug("Loaded RGB object detection model.")
        # TODO send search classes to PiB
        rgb_model.set_classes(CLASSES)
        logger.info(f"Set YOLO classes to {CLASSES}.")
        
        logger.info("Setup complete. Waiting to start capture...")

        # Poll for trigger capture signal
        while commsHandlerInstance.is_connected():
            # logger.info(f"Queue Size: {commsHandlerInstance.receive_queue.qsize()}")
            
            # Process incoming messages 
            commsHandlerInstance.process_messages(child_message_handler)
            sleep(1)

            if received_objects:
                objects += received_objects

            received_objects = [] # Clear objects

    
    except Exception as e:
        logger.error(f"Error in PiB.py: {e}")

        if ENABLE_HS:
            axis.move_absolute(2,Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True) # temporarily blocking
            hs_cam.Close()
            zaber_conn.close()

    except KeyboardInterrupt:
        logger.info("Shutting down")
        commsHandlerInstance.stop()

    # finally:
    #     if ENABLE_HS:
    #         axis.move_absolute(2,Units.ANGLE_DEGREES,velocity=80,velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,wait_until_idle=True) # temporarily blocking
    #         hs_cam.Close()
    #         zaber_conn.close()
    #     commsHandlerInstance.stop()
    #     logger.info("All connections closed.")
    #     logger.info("System terminated.")
    


