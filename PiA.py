from object_detection.object_detection import *
from comms.receive import *
from comms.send import *
from gps.gps import Neo8T
from datetime import datetime
from time import sleep
from comms.updateJSON import *
import cv2
from cameras import *
import logging 
from stitching.stitching_main import performPanoramicStitching
import json

# Triggers when change in GPS location
def new_scan(rgb_model, activeFile, lon=55.3, lat=-4,privacy=False):
    # Captures two images
    setStatusMessage("capturing images")
    frames = capture(cams, "PiA")
    # Triggers capture on PiB
    request_client_capture(server_socket, conn)
    setStatusMessage("detecting objects")
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model,f))
    # Retrieve slave images and data
    frames += receive_image_arrays(conn)
    # Send object detection results to PiB
    send_object_detection_results(conn, objects)  
    # Receive object detection data
    objects += receive_object_detection_results(conn)

    # Blur people if privacy 
    setStatusMessage("blurring people")
    if privacy:
        for i in range(len(frames)):
            frames[i] = blur_people(frames[i],objects[i],255)

    setStatusMessage("stitching images")
    # Perform pano stitching
    panorama, objects = performPanoramicStitching(frames, objects)
    # Restructure objects
    objects_restructured = []
    for frame in objects:
        objects_restructured += frame
    
    # Remove duplicate object detections
    setStatusMessage("removing duplicate objects")
    filtered_objects = non_maximum_suppression(objects_restructured)

    # TODO: Receive hsi photo and data 
    # Updates json and moves images to correct folder
    setStatusMessage("final touches")
    uid = str(lon)+str(lat)
    for i in range(len(filtered_objects)):
        filtered_objects[i][1] = xyxy_to_xywh(filtered_objects[i][1], panorama.shape[1], panorama.shape[0], True)

    updateJSON(uid, lon, lat, filtered_objects, panorama, activeFile)
    setStatusMessage("complete!")

PORT = 5002
HOST = "0.0.0.0" # i.e. listening
RESOLUTION = (4608,2592)
FOV = (102,67)
PRIVACY = True  #Blur people
CLASSES = ["person"] 

# GPS
GPS_PORT = "/dev/ttyACM0" # USB Port (check automatically?)
GPS_BAUDRATE = 115200
DISTANCE_THRESHOLD = 10

if __name__ == "__main__":
    setStatusMessage("setting up")
    # Setup Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",style="{",datefmt="%Y-%m-%d %H:%M",
        handlers=[
        logging.FileHandler("piA.log"),
        logging.StreamHandler()
        ])
    logging.info("##### Start up new sesson. #####")
    # Setup cameras and GPIO
    cams = setup_cameras()
    logging.debug("Setup cameras.")
    # Setup GPS 
    gps = Neo8T(port=GPS_PORT, baudrate=GPS_BAUDRATE,timeout=1,distance_threshold=DISTANCE_THRESHOLD)
    logging.debug("Setup GPS")
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
    
    #Mainloop
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
            # Trigger new scan 
            new_scan(rgb_model,activeFile, lat=location["latitude"], lon=location["longitude"], privacy=PRIVACY)       
        
            logging.info("Completed scan.")

            if status == 2:
                setPlatformStatus(0)
