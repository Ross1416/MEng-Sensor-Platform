from object_detection.object_detection import *
from comms.receive import *
from datetime import datetime
from time import sleep
from comms.updateJSON import updateJSON
import cv2
from cameras import *

# Triggers when change in GPS location
def new_scan(rgb_model, lon=0.00, lat=0.00):
    # Captures 2 images
    frames = capture(cams, "PiA", save_location)
    # Triggers capture on PiB
    request_client_capture(server_socket, conn)
    # Perform object detection
    objects = []
    for f in frames:
        objects.append(object_detection(rgb_model,f))
    # Retrieve slave images and data
    receive_images(save_location, server_socket, conn)  
    # send rotational stage control signal
    pixel_to_angle((50,100),RESOLUTION,FOV)
    # Perform pano stitching
    # Receive hsi photo and data 
    # Updates json and moves images to correct folder
    #TODO (SD): update json test script
    uid = str(lon)+str(lat)
    updateJSON(uid, lon, lat, objects)

PORT = 5002
HOST = "0.0.0.0" # i.e. listening
RESOLUTION = (4608,2592)
FOV = (102,67)

if __name__ == "__main__":
    # Setup cameras and GPIO
    cams = setup_cameras()
    # Make connection
    server_socket, conn = make_server_connection(HOST, PORT)
    # Setup object detection model
    rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")

    #Mainloop
    while True:
        # TODO: Check for location change
        # Update save location
        timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        save_location = f"./capture/{timestamp}-capture/"

        new_scan(rgb_model)       
        print("Completed scan!") 
        cv2.waitKey(0)
