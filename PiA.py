from object_detection.object_detection import *
from comms.receive import *
from datetime import datetime
from time import sleep

# Triggers when change in GPS location
def new_scan(rgb_model):
    # Captures 2 images
    frames = capture(cams, "PiA", save_location)
    # Triggers capture on PiB
    request_client_capture(server_socket, conn)
    # Perform object detection
    results = []
    for f in frames:
        results.append(object_detection(rgb_model,f))
    # Retrieve slave images and data
    receive_images(save_location, server_socket, conn)  
    # send rotational stage control signal
    #TODO write function to translate pixel coords to angle
    # Perform pano stitching
    # Receive hsi photo and data 
    # Updates json and moves images to correct folder
    #TODO (SD): update json test script

PORT = 5002
HOST = "0.0.0.0" # i.e. listening

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
        break

