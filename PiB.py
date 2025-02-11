from object_detection.object_detection import *
from comms.send import *
from cameras import *
from time import sleep

def on_trigger(rgb_model):
    # Capture images
    frames = capture(cams, "PiB", PATH)
    # Perform object detection
    results = []
    for f in frames:
        results.append(object_detection(rgb_model,f))
    # Send images to PiA
    send_images(path, client_socket)
    

def on_rotate():
    # Rotate rotational stage 
    # take hsi image
    # process hsi image
    # return hsi colour image and data
    pass


# IP = "10.12.23.188"
IP = "hsiA.local"
PORT = 5002
PATH = "./captures/"

if __name__ == "__main__":
    try:
        # Setup cameras and capture images
        cams = setup_cameras()
        # Make connection with PiA
        client_socket = make_client_connection(IP, PORT)
        # Setup object detection model
        rgb_model = YOLOWorld("object_detection/yolo_models/yolov8s-worldv2.pt")

        # Poll for trigger capture signal
        capture_triggered = False
        while not capture_triggered:
            if receive_capture_request(client_socket) == 1:
                on_trigger(rgb_model)
                capture_triggered = True
        

    except Exception as e:
        print(f"Error in PiB.py: {e}")

    finally:
        client_socket.close()
    

