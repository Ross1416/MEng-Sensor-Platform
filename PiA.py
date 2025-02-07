from object_detection.object_detection import *
from comms.receive import *
from datetime import datetime
from time import sleep

# Triggers when change in GPS location
def new_scan():
    # Captures 2 images
    # Perform object detectio 
    # Retreive slave images and data
    # send rotational stage control signal
    # Perform pano stitching
    # Receive hsi photo and data 
    # Updates json and moves images to correct folder
    pass

TRIGGER_PIN=26

if __name__ == "__main__":
    try:
        # Setup cameras and GPIO
        cams = setup_cameras()

        port = 5002
        host = "0.0.0.0" # i.e. listening

        timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        save_location = f"./capture/{timestamp}-capture/"
        
        server_socket, conn = make_server_connection(host, port)
        
        # Trigger capture on PiB

        capture(cams, "PiA", save_location)
        request_client_capture(server_socket, conn)
        receive_images(save_location, server_socket, conn)
        sleep(1)
    
    except Exception as e:
        print(f"Error in PiA.py: {e}")