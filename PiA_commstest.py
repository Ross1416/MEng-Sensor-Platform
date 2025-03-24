from object_detection.object_detection import *
from comms.comms_oop import *
from datetime import datetime
from time import sleep
from comms.updateJSON import updateJSON, getPlatformStatus, setPlatformStatus
import cv2
from cameras import *
import logging 
from stitching.stitching_main import performPanoramicStitching
import json

def new_scan(rgb_model, activeFile, commsHandler, lon=55.3, lat=-4, privacy=False):
    # Capture two images on PiA
    frames = capture(cams, "PiA")
    
    # Trigger capture on PiB
    commsHandler.request_capture()
    
    # Wait for child frames
    child_frames = []
    start_time = datetime.now()
    while len(child_frames) == 0 and (datetime.now() - start_time).seconds < 10:
        message_type, payload = commsHandler.get_message(block=False)
        if message_type == MessageType.IMAGE_FRAMES:
            child_frames = payload
            logging.info(f"Received {len(child_frames)} frames from child")
    
    # Combine frames from both platforms
    frames.extend(child_frames)
    
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model, f))
    
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

    # Update json and move images
    uid = str(lon) + str(lat)
    for i in range(len(filtered_objects)):
        filtered_objects[i][1] = xyxy_to_xywh(filtered_objects[i][1], panorama.shape[1], panorama.shape[0], True)

    updateJSON(uid, lon, lat, filtered_objects, panorama, activeFile)

def parent_message_handler(message_type, payload):
    print(f"Received message type: {message_type}")
    match message_type:
        case MessageType.CONNECT:
            logging.info("Child connected")
            return True
        case MessageType.DISCONNECT:
            logging.info("Child disconnected")
            return True
        case MessageType.HEARTBEAT:
            print("Heartbeat received")
            return True
        case MessageType.IMAGE_FRAMES:
            logging.info(f"Received {len(payload)} frames from child")
            return True        
        case MessageType.OBJECT_DETECTION:
            logging.info(f"Received object detection data from child")
            return True
        case MessageType.ERROR:
            logging.error(f"Communication error: {payload}")
            return True
        case _:
            return False


PORT = 5002
HOST = "0.0.0.0" # i.e. listening
RESOLUTION = (4608,2592)
FOV = (102,67)
PRIVACY = True  #Blur people
CLASSES = ["person"] 

if __name__ == "__main__":
    # Setup Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        handlers=[
            logging.FileHandler("piA.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("PiA")
    logger.info("##### Start up new sesson. #####")

    # Setup comms handler instance
    commsHandlerInstance = CommsHandler(is_parent=True, host=HOST, port=PORT)
    commsHandlerInstance.start()

    # Setup cameras and GPIO
    cams = setup_cameras()
    logger.debug("Setup cameras.")
    # Make connection
    # server_socket, conn = make_server_connection(HOST, PORT)
    # logger.debug("Connected to PiB")
    # Setup object detection model
    rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
    logger.debug("Loaded RGB object detection model.")
    rgb_model.set_classes(CLASSES)
    logger.info(f"Set YOLO classes to {CLASSES}.")
    logger.info(f"Privacy set {PRIVACY}.")
    logger.info(f"Waiting for trigger...")
    sleep(0.5)
    
    # message_type, payload = None, None
    # while message_type != MessageType.CONNECT:
    #     message_type, payload = commsHandlerInstance.get_message(timeout=10)
    #     if message_type == MessageType.CONNECT:
    #         continue

    if commsHandlerInstance.is_connected():
        logger.info("Entering Main Loop now")
        #Mainloop
        try:
            while True:
                print("Processing messages...")
                commsHandlerInstance.process_messages(parent_message_handler)
                # TODO: Check for location change
                # Update save location
                try:
                    status, activeFile = getPlatformStatus()
                except json.decoder.JSONDecodeError:
                    logger.error("Error accessing JSON configuration file.")    
                GPS_coordinate_change = True

                if status == 2 or (status == 1 and GPS_coordinate_change):
                    timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                    save_location = f"./capture/{timestamp}-capture/"
                    
                    new_scan(rgb_model, activeFile, commsHandlerInstance, privacy=PRIVACY)       

                    logger.info("Completed scan.")
    
                    print("Processing messages...")
                    commsHandlerInstance.process_messages(parent_message_handler)

                    if status == 2:
                        setPlatformStatus(0)

        except KeyboardInterrupt:
            logger.info("Shutting down")
            commsHandlerInstance.stop()
        # finally:
        #     commsHandlerInstance.stop()
