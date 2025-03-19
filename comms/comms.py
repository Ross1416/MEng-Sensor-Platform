import os
import socket
from os import listdir
from time import sleep
import pickle
import logging
import cv2

def check_connection(remote="www.google.com", port=80, timeout=3):
    try:
        with socket.create_connection((remote, port), timeout) as sock:
            return True
    except socket.error as e:
        print(f"Connection failed: {e}")
        return False

def make_server_connection(host, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host,port))
        server_socket.listen(1)
        print(f"Server listening on {host}:{port}")

        # Accept a connection
        conn, addr = server_socket.accept()
        print(f"Connection established with {addr}")

        return server_socket, conn
    except Exception as e:
        print(f"Error: {e}")

def make_client_connection(ip, port):
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, port))
            print(f"Connected to {ip}:{port}")
            print(type(client_socket))
            return client_socket
        except ConnectionRefusedError:
            print("Connection failed, retrying in 2 seconds...")
            sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            sleep(2)

def request_client_capture(server_socket, conn):
    try:
        conn.sendall(b"CAPTURE REQUEST")
        print("Capture request sent")
    except Exception as e:
        print("Error: {e}")

def receive_capture_request(client_socket):
    try:
        ack = client_socket.recv(1024).decode()
        if ack != "CAPTURE REQUEST":
            print("No capture request made.")
            return
        print("Capture request received.")
        sleep(2)    
        return 1
        
    except Exception as e:
        print(f"Error: {e}")
        sleep(1)
        # client_socket.close()
        return 0

def send_image_arrays(client_socket, frames):
    """Takes in an array of frames and sends them over socekt"""
    # Send number of frames to expect
    logging.debug(f"Sending {len(frames)} frames.")
    client_socket.send(len(frames).to_bytes(8, byteorder='big'))
    # Send all images
    for img in frames:
        img = cv2.imencode('.jpg', img)[1] # Compress image
        data = pickle.dumps(img)
        logging.debug(f"Sending frame of size {len(data)}")
        client_socket.send(len(data).to_bytes(8, byteorder='big'))
        client_socket.sendall(data)
        logging.debug(f"Frame sent.")

def receive_image_arrays(conn):
    # Get number of images
    num_images = conn.recv(8)   
    if not num_images:
        return []
    num_images = int.from_bytes(num_images, byteorder='big')
    logging.debug(f"Receiving {num_images} frames.")

    frames = []
    if num_images:
        for i in range(num_images):
            logging.debug(f"Receiving frame {i}.")

            data_size = conn.recv(8)  # First 8 bytes for size
            if not data_size:
                break
            data_size = int.from_bytes(data_size, byteorder='big')
            logging.debug(f"Receiving frame {i} of size {data_size}.")
            data = b""
            while len(data) < data_size:
                packet = conn.recv(min(4096, data_size - len(data)))
                if not packet:
                    logging.error(f"Packet lost.")
                    break
                data += packet
            logging.debug(f"Frame received.")

            img = pickle.loads(data)
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)
            frames.append(img)

    return frames


def send_object_detection_results(client_socket, objects):
    """Send object detection results to PiB over socket"""
    try:
        # Send number of objects
        client_socket.send(len(objects).to_bytes(8, byteorder='big'))
        # Send all objects
        for obj in objects:
            # Serialise the data
            data = pickle.dumps(obj)
            logging.debug(f"Sending object detection data of size {len(data)}")
            client_socket.send(len(data).to_bytes(8, byteorder='big'))
            client_socket.sendall(data)
            logging.debug(f"Object detection data sent.")

    except Exception as e:
        print(f"Error: {e}")

def receive_object_detection_results(client_socket):
    # Get number of objects
    num_objects = client_socket.recv(8)   
    if not num_objects:
        return []
    num_objects = int.from_bytes(num_objects, byteorder='big')
    logging.debug(f"Receiving {num_objects} objects.")

    objects = []
    if num_objects:
        for i in range(num_objects):
            logging.debug(f"Receiving object object detection data {i}.")

            data_size = client_socket.recv(8)  # First 8 bytes for size
            if not data_size:
                break
            data_size = int.from_bytes(data_size, byteorder='big')
            logging.debug(f"Receiving object detection data {i} of size {data_size}.")
            data = b""
            while len(data) < data_size:
                packet = client_socket.recv(min(4096, data_size - len(data)))
                if not packet:
                    logging.error(f"Packet lost.")
                    break
                data += packet
            logging.debug(f"Object detection data received.")

            obj = pickle.loads(data)
            objects.append(obj)

    return objects

def send_images(client_socket, folder_path):
    try:
        # get the path/directory of the photos taken locally on the child Pi
        images = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print("No images found")
            return

        print(len(images))
        client_socket.sendall(f"{len(images)}".encode())

        for image in images:
            image_path = os.path.join(folder_path, image)
            print(f"Getting ready to send {image}...")
            print(image_path)
            filesize = os.path.getsize(image_path)
            filename = os.path.basename(image_path)
            client_socket.sendall(f"{filename}|{filesize}".encode())
            # Wait for acknowledgment
            print("Waiting for acknowledgement...")
            ack = client_socket.recv(1024).decode()
            if ack != "READY":
                print("Server is not ready to receive the file.")
                return
            print("Acknowledgement received.")
            # Send the image file
            with open(image_path, "rb") as file:
                while (chunk := file.read(1024)):
                    client_socket.sendall(chunk)
            
            print(f"Image {filename} sent successfully!")
            sleep(1)
        
        print("All images sent!")
    
    except Exception as e:
        print(f"Error: {e}")

def receive_images(conn, save_location):
    try:
        os.makedirs(save_location, exist_ok=True)
        
        # Send acknowledgment
        num_images = int(conn.recv(1024).decode())
        conn.sendall(b"READY")
        print("READY")
        print(f"Expecting {num_images} images.")

        for i in range(num_images):
            print(i)
            # Receive image metadata
            metadata = conn.recv(1024).decode()
            filename, file_size = metadata.split("|")
            file_size = int(file_size)

            # Prepare to receive the file
            save_path = os.path.join(save_location, filename)
            print(save_path)
            with open(save_path, "wb") as file:
                received_size = 0
                print("00000")
                while received_size < file_size:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    file.write(chunk)
                    received_size += len(chunk)
            print(f"Image received and saved at {save_path}")
            conn.sendall(b"READY")


    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if check_connection():
        print("The Internet is connected.")
    else:
        print("The Internet is not connected.")

    if check_connection("192.168.1.59"):
        print("The Pi is connected.")
    else:
        print("The Pi is not connected.")