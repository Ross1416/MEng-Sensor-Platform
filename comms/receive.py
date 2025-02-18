# Deploy on the "parent" device i.e. PiA to allow it to receive information from the "child" device i.e. PiB

import socket
import os
import pickle

def make_server_connection(host, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    frames = []
    if num_images:
        for img in num_images:
            data_size = conn.recv(8)  # First 8 bytes for size
            if not data_size:
                break
            data_size = int.from_bytes(data_size, byteorder='big')
            data = b""
            while len(data) < data_size:
                packet = conn.recv(4096)  # Receive in chunks
                if not packet:
                    break
                data += packet
            frames.append(pickle.loads(data))

    return frames

if __name__ == "__main__":
    port = 5002
    host = "0.0.0.0" # i.e. listening
    save_location = "./received_images"

    server_socket, conn = make_server_connection(host, port)
    
    request_client_capture(server_socket, conn)
    receive_images(save_location, server_socket, conn)