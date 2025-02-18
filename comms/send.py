# Deploy on the "child" device i.e. PiB to allow it to communicate with the "parent" device i.e. PiA

import os
import socket
from os import listdir
from time import sleep
import logging

def make_client_connection(ip, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        logging.info(f"Connected to {ip}:{port}")
        return client_socket
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return


def list_images(folder_path, client_socket):
    # get the path/directory
        images = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            logging.info("No images found")
            client_socket.close()
            return

        print(len(images))
        client_socket.sendall(f"{len(images)}".encode())

        for image in images:
            image_path = os.path.join(folder_path, image)
            logging.info(f"Getting ready to send {image}...")
            filesize = os.path.getsize(image)
            
            filename = os.path.basename(image)

            client_socket.sendall(f"{filename}|{filesize}".encode())

            # Wait for acknowledgment
            print("Waiting for acknowledgement...")
            ack = client_socket.recv(1024).decode()
            if ack != "READY":
                logging.warning("Server is not ready to receive the file.")
                return
            logging.info("Acknowledgement received.")
            # Send the image file
            with open(image_path, "rb") as file:
                while (chunk := file.read(1024)):
                    client_socket.sendall(chunk)
            
            logging.info(f"Image {filename} sent successfully!")
        
        logging.info("All images sent!")
        return

def send_images(folder_path, client_socket):
    try:
        # get the path/directory of the photos taken locally on the child Pi
        images = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            logging.warning("No images found")
            client_socket.close()
            return

        logging.info(f"{len(images)} images found")
        client_socket.sendall(f"{len(images)}".encode())

        for image in images:
            image_path = os.path.join(folder_path, image)
            logging.info(f"Getting ready to send {image}...")
            logging.info(f"Sending image to \"{image_path}\"")
            filesize = os.path.getsize(image_path)
            filename = os.path.basename(image_path)
            client_socket.sendall(f"{filename}|{filesize}".encode())
            # Wait for acknowledgment
            logging.info("Waiting for acknowledgement...")
            ack = client_socket.recv(1024).decode()
            if ack != "READY":
                logging.warning("Server is not ready to receive the file.")
                return
            logging.info("Acknowledgement received.")
            # Send the image file
            with open(image_path, "rb") as file:
                while (chunk := file.read(1024)):
                    client_socket.sendall(chunk)
            
            logging.info(f"Image {filename} sent successfully!")
            sleep(1)
        
        logging.info("All images sent!")
    
    except Exception as e:
        logging.error(f"Error: {e}")

    finally:
        client_socket.close()

def receive_capture_request(client_socket):
    try:
        ack = client_socket.recv(1024).decode()
        if ack != "CAPTURE REQUEST":
            logging.warning("No capture request made.")
            return
        logging.info("Capture request received.")
        sleep(2)    
        return 1
        
    except Exception as e:
        logging.error(f"Error: {e}")
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
