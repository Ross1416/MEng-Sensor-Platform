# Deploy on the "child" device i.e. PiB to allow it to communicate with the "parent" device i.e. PiA

import os
import socket
from os import listdir
from time import sleep
import pickle
import logging
import cv2

def make_client_connection(ip, port):
    # TODO: Add timeout?
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


def list_images(folder_path, client_socket):
    # get the path/directory
        images = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print("No images found")
            client_socket.close()
            return

        print(len(images))
        client_socket.sendall(f"{len(images)}".encode())

        for image in images:
            image_path = os.path.join(folder_path, image)
            print(f"Getting ready to send {image}...")
            filesize = os.path.getsize(image)
            
            filename = os.path.basename(image)

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
        
        print("All images sent!")
        return

def send_images(folder_path, client_socket):
    try:
        # get the path/directory of the photos taken locally on the child Pi
        images = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print("No images found")
            client_socket.close()
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

    finally:
        client_socket.close()

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

if __name__ == "__main__":
    ip = "10.12.23.188"
    test_ip = "10.12.71.113"
    port = 5002
    path = "./captures/"

    client_socket = make_client_connection(test_ip, port)

    while(1):
        receive_capture_request(client_socket)
        send_images(path, client_socket)
