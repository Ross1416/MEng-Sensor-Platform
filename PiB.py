from object_detection.object_detection import *
from comms.send import *
from comms.receive import * 
from cameras import *
from time import sleep
import logging

def on_trigger(rgb_model):
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
    # send_images(PATH, client_socket)
    send_image_arrays(client_socket,frames)
    # Send object detection results to PiA
    send_object_detection_results(client_socket, objects[2:])  
    

def on_rotate():
    # Rotate rotational stage 
    # take hsi image
    # process hsi image
    # return hsi colour image and data
    pass


# IP = "10.12.101.192"
IP = "hsiA.local"
PORT = 5002
PATH = "./captures/"
CLASSES = ["person"] 

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
                on_trigger(rgb_model)
                capture_triggered = True
            
            sleep(1)
        

    except Exception as e:
        print(f"Error in PiB.py: {e}")

    finally:
        client_socket.close()
    

