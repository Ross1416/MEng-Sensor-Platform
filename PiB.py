from object_detection.object_detection import *
from comms.send import *
from cameras import *
from time import sleep
import logging

def on_trigger(rgb_model):
    # Capture images
    frames = capture(cams, "PiB", PATH)
    # Perform object detection
    results = []
    for f in frames:
        results.append(object_detection(rgb_model,f))
    # Send images to PiA
    # send_images(PATH, client_socket)
    send_image_arrays(client_socket,frames)
    

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
CLASSES = ["person","face"] 

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

        # Poll for trigger capture signal
        while True:
            if receive_capture_request(client_socket) == 1:
                logging.info("Triggered Capture.")
                on_trigger(rgb_model)
                capture_triggered = True
            
            receive_object_detection_results(client_socket)
            sleep(1)
        

    except Exception as e:
        print(f"Error in PiB.py: {e}")

    finally:
        client_socket.close()
    

