# Deploy on the "parent" device i.e. PiA to allow it to receive information from the "child" device i.e. PiB

import socket
import os
import pickle
import logging
import cv2

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

def request_client_capture(server_socket, conn):
    try:
        conn.sendall(b"CAPTURE REQUEST")
        print("Capture request sent")
    except Exception as e:
        print("Error: {e}")

    

def receive_images(save_location, server_socket, conn):
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

    finally:
        server_socket.close()
        print("Connection ended.")

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
            logging.debug(f"Sending frame of size {len(data)}")
            client_socket.send(len(data).to_bytes(8, byteorder='big'))
            client_socket.sendall(data)
            logging.debug(f"Frame sent.")

    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    port = 5002
    host = "0.0.0.0" # i.e. listening
    save_location = "./received_images"

    server_socket, conn = make_server_connection(host, port)
    
    request_client_capture(server_socket, conn)
    receive_images(save_location, server_socket, conn)