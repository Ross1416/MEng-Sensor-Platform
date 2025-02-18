from object_detection.object_detection import *
from comms.receive import *
from datetime import datetime
from time import sleep
from comms.updateJSON import updateJSON
import cv2
from cameras import *
import logging 
from stitching.stitching_main import performPanoramicStitching

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
    # receive_images(save_location, server_socket, conn)  
    b_frames = receive_image_arrays(conn)
    print(f"length of frames before {len(frames)}")
    frames.append(b_frames)
    print(f"length of frames after {len(frames)}")

    # send rotational stage control signal
    angle_x, _ = pixel_to_angle((50,100),RESOLUTION,FOV)
    # Perform pano stitching
    # TO DO: clean this up
    image3 = cv2.imread(save_location+'PiB_0.jpg')
    image4 = cv2.imread(save_location+'PiB_1.jpg')
    panorama = performPanoramicStitching(frames[0], frames[1], image3, image4)
    # Receive hsi photo and data 
    # Updates json and moves images to correct folder
    uid = str(lon)+str(lat)
    updateJSON(uid, lon, lat, objects, panorama)

PORT = 5002
HOST = "0.0.0.0" # i.e. listening
RESOLUTION = (4608,2592)
FOV = (102,67)

if __name__ == "__main__":
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
    # Make connection
    server_socket, conn = make_server_connection(HOST, PORT)
    logging.debug("Connected to PiB")
    # Setup object detection model
    rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")
    logging.debug("Loaded RGB object detection model.")

    #Mainloop
    while True:
        # TODO: Check for location change
        # Update save location
        timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        save_location = f"./capture/{timestamp}-capture/"

        new_scan(rgb_model)       
        logging.info("Completed scan.")
        input("Press key to continue...")
