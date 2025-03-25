from object_detection.object_detection import *
from comms.comms_oop import *
from datetime import datetime
from time import sleep
import numpy as np
from comms.updateJSON import updateJSON, getPlatformStatus, setPlatformStatus
import cv2
from cameras import *
import logging 
from stitching.stitching_main import performPanoramicStitching
import json
import queue
import os

os.makedirs("./debug_child_frames", exist_ok=True)

def new_scan(rgb_model, activeFile, commsHandler, lon=55.3, lat=-4, privacy=False):
    # Capture two images on PiA
    frames = capture(cams, "PiA")
    
    # Trigger capture on PiB
    commsHandlerInstance.request_capture()
    sleep(30)

        # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model,f))

    logging.info("Sending object detection results...")
    commsHandlerInstance.send_object_detection_results(objects)

    print(objects)
    
    return frames, objects

    # # Combine frames from both platforms
    # frames.extend(child_frames)
    
    # # Perform object detection
    # objects = []
    # for f in frames:
    #     objects.append(object_detection(rgb_model, f))
    
    # # Blur people if privacy 
    # if privacy:
    #     for i in range(len(frames)):
    #         frames[i] = blur_people(frames[i], objects[i], 255)

    # # Perform pano stitching
    # panorama, objects = performPanoramicStitching(frames, objects)
    
    # # Restructure objects
    # objects_restructured = []
    # for frame in objects:
    #     objects_restructured += frame
    
    # # Remove duplicate object detections
    # filtered_objects = non_maximum_suppression(objects_restructured)

    # # Update json and move images
    # uid = str(lon) + str(lat)
    # for i in range(len(filtered_objects)):
    #     filtered_objects[i][1] = xyxy_to_xywh(filtered_objects[i][1], panorama.shape[1], panorama.shape[0], True)

    # updateJSON(uid, lon, lat, filtered_objects, panorama, activeFile)


received_frames = []
received_objects = []
def parent_message_handler(message_type, payload):
    global received_frames
    global received_objects
    match message_type:
        case MessageType.CONNECT:
            logging.info("Child connected")
            return True
        case MessageType.DISCONNECT:
            logging.info("Child disconnected")
            return True
        case MessageType.HEARTBEAT:
            return True
        case MessageType.IMAGE_FRAMES:
            logging.info(f"Received image frames payload of type {type(payload)}")
            try:
                # The payload should be a list of compressed frames
                if not isinstance(payload, list):
                    payload = [payload]
                # Decode each frame
                decoded_frames = []
                for i, compressed_frame in enumerate(payload):
                    try:
                        # Convert compressed frame to numpy array
                        nparr = np.frombuffer(compressed_frame, np.uint8)
                        # Decode image
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if img is not None:
                            decoded_frames.append(img)
                            # Save for debugging
                            cv2.imwrite(f"./debug_child_frames/child_frame_{i}.jpg", img)
                        else:
                            logging.error(f"Failed to decode frame {i}")
                    except Exception as e:
                        logging.error(f"Error decoding frame {i}: {e}")
                
                received_frames.extend(decoded_frames)
                logging.info(f"Successfully decoded {len(decoded_frames)} frames")
                return True
            except Exception as e:
                logging.error(f"Error processing frames: {e}")
                return False

        case MessageType.OBJECT_DETECTION:
            received_objects = payload
            logging.info(f"Received object detection data from child")
            logging.info(f"{received_objects}")
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
lon=55.3
lat=-4

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

    # if commsHandlerInstance.is_connected():
    #     logger.info("Entering Main Loop now")
    #     #Mainloop
    #     try:
    #         while True:
    #             print("Processing messages...")
    #             commsHandlerInstance.process_messages(parent_message_handler)
    #             # TODO: Check for location change
    #             # Update save location
    #             try:
    #                 status, activeFile = getPlatformStatus()
    #             except json.decoder.JSONDecodeError:
    #                 logger.error("Error accessing JSON configuration file.")    
    #             GPS_coordinate_change = True

    #             if status == 2 or (status == 1 and GPS_coordinate_change):
    #                 timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    #                 save_location = f"./capture/{timestamp}-capture/"
                    
    #                 new_scan(rgb_model, activeFile, commsHandlerInstance, privacy=PRIVACY)       

    #                 logger.info("Completed scan.")
    
    #                 print("Processing messages...")
    #                 commsHandlerInstance.process_messages(parent_message_handler)

    #                 if status == 2:
    #                     setPlatformStatus(0)

    #     except KeyboardInterrupt:
    #         logger.info("Shutting down")
    #         commsHandlerInstance.stop()
    #     # finally:
    #     #     commsHandlerInstance.stop()

    # frames = capture(cams, "PiA")
    # Trigger capture on PiB
    # commsHandlerInstance.request_capture()
    status, activeFile = getPlatformStatus()
    frames, objects = new_scan(rgb_model, activeFile, commsHandlerInstance, privacy=PRIVACY)
    try:
        while True:
            # logger.info(f"Queue Size: {commsHandlerInstance.receive_queue.qsize()}")
            # Process incoming messages 
            commsHandlerInstance.process_messages(parent_message_handler)  
            sleep(1)
            
            logger.info(f"Current state - Frames: {len(received_frames)}, Objects: {len(received_objects)}")

            if received_frames and received_objects:
                logging.info(f"Processing {len(received_frames)} received frames")
                frames +=  received_frames
                objects += received_objects
                panorama, objects = performPanoramicStitching(frames, objects)

                # Do stuff
                # Blur people if privacy 
                if PRIVACY:
                    for i in range(len(received_frames)):
                        frames[i] = blur_people(received_frames[i],objects[i],255)

                # Perform pano stitching
                panorama, objects = performPanoramicStitching(received_frames, objects)
                # Restructure objects
                objects_restructured = []
                for frame in objects:
                    objects_restructured += frame
                
                # Remove duplicate object detections
                filtered_objects = non_maximum_suppression(objects_restructured)

                # TODO: Receive hsi photo and data 
                # Updates json and moves images to correct folder
                uid = str(lon)+str(lat)
                for i in range(len(filtered_objects)):
                    filtered_objects[i][1] = xyxy_to_xywh(filtered_objects[i][1], panorama.shape[1], panorama.shape[0], True)

                updateJSON(uid, lon, lat, filtered_objects, panorama, activeFile)

                received_frames = [] # Clear the frames
                received_objects = [] # Clear objects
                print("Finished!")

    except KeyboardInterrupt:
        logger.info("Shutting down")
        commsHandlerInstance.stop()