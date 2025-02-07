from object_detection.object_detection import *
from comms.send import *
from cameras import *
from time import sleep

def on_trigger():
    # Capture images
    # Perform object detection
    # Send slave images and  data
    pass

def on_rotate():
    # Rotate rotational stage 
    # take hsi image
    # process hsi image
    # return hsi colour image and data
    pass


TRIGGER_PIN=26
last = 0

if __name__ == "__main__":
    try:
        # Setup cameras and capture images
        cams = setup_cameras()
    
        # ip = "10.12.23.188"
        ip = "hsiA.local"
        port = 5002
        path = "./captures/"
  
        client_socket = make_client_connection(ip, port)

        # Poll for trigger capture signal
        capture_triggered = False
        while not capture_triggered:
            if receive_capture_request(client_socket) == 1:
                print("Triggered Capture")
                capture(cams, "PiB", path)
                sleep(4)
                send_images(path, client_socket)
                capture_triggered = True
        

    except Exception as e:
        print(f"Error in PiB.py: {e}")

    finally:
        client_socket.close()
    

