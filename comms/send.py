# Deploy on the "child" device i.e. PiB to allow it to communicate with the "parent" device i.e. PiA

import os
import socket
from os import listdir
from time import sleep

def make_client_connection(ip, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        print(f"Connected to {ip}:{port}")
        print(type(client_socket))
        return client_socket
    
    except Exception as e:
        print(f"Error: {e}")
        return


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
    
    except Exception as e:
        print(f"Error: {e}")

    finally:
        client_socket.close()

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
        print(f"Exception: {e}")
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
