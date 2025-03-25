# Object-Oriented Version of Comms Code

import logging
import socket
import pickle
import queue
import threading
from enum import Enum, auto
from time import sleep #for testing only in the __name__ == '__main__'
import argparse
import cv2

HOST = "0.0.0.0" # i.e. listening
# HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050

class MessageType(Enum):
    CONNECT = auto()
    DISCONNECT = auto()
    CAPTURE_REQUEST = auto()
    IMAGE_FRAMES = auto()
    OBJECT_DETECTION = auto()   # Sending/receiving object detection results data
    HEARTBEAT = auto()
    ERROR = auto()
    # HYPERSPECTRAL_DATA = auto()

class CommsHandler():
    def __init__(self, is_parent=True, host=HOST, port=PORT, remote_host=None):
        ''' The default version of CommsHandler is the server (parent) '''
        self.is_parent = is_parent
        self.host = host
        self.port = port
        self.remote_host = remote_host
        self.socket = None
        self.conn = None
        self.connected = False
        self.running = False

        # Start logging
        self.logger = logging.getLogger("CommsHandler")
        self.logger.info("Logger online!")

        # Setup queues for sending and receiving
        self.send_queue = queue.Queue()
        self.receive_queue = queue.Queue()

        # Threads
        self.listener_thread = None
        self.sender_thread = None
        self.heartbeat_thread = None


    def start(self):
        if self.running:
            return
        self.running = True
        if self.is_parent:
            self._start_server()
        else:
            self._start_client()

        # Start worker threads
        self.listener_thread = threading.Thread(target=self._listener_worker, daemon=True)
        self.sender_thread = threading.Thread(target=self._sender_worker, daemon=True)
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        
        self.listener_thread.start()
        self.sender_thread.start()
        self.heartbeat_thread.start()
        
        self.logger.info(f"CommsHandler started as {'parent' if self.is_parent else 'child'}")

    def stop(self):
        """Stop the communication service"""
        self.running = False
        self.connected = False
        
        # Send disconnect message
        # self.send_message(MessageType.DISCONNECT, None)
        
        # Wait for threads to finish
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2)
        if self.sender_thread and self.sender_thread.is_alive():
            self.sender_thread.join(timeout=2)
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)
            
        # Close socket connections
        if self.conn:
            self.conn.close()
        if self.socket:
            self.socket.close()
            
        self.logger.info("CommsHandler stopped")

    def _start_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host,self.port))
            self.socket.settimeout(5)  # 5 second timeout for accept
            self.socket.listen(1)
            self.logger.info(f"Server listening on {self.host}:{self.port}")

            # Start accept thread
            threading.Thread(target=self._accept_connections, daemon=True).start()

            # return socket, conn
        except Exception as e:
            self.logger.error(f"Error while starting parent server: {e}")
            self.running = False
        
        finally:
            print("Exiting startup function")

    def _start_client(self):
        """Start client and connect to server"""
        def connect_thread():
            while self.running and not self.connected:
                try:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.settimeout(20)  # 5 second timeout
                    self.socket.connect((self.remote_host, self.port))
                    self.connected = True
                    self.conn = self.socket  # For consistency with server code
                    self.logger.info(f"Connected to {self.remote_host}:{self.port}")
                    
                    # Add CONNECT message to receive queue to process
                    self.receive_queue.put((MessageType.CONNECT, None))
                except ConnectionRefusedError:
                    self.logger.warning("Connection refused, retrying in 5 seconds...")
                    sleep(5)
                except Exception as e:
                    self.logger.error(f"Error connecting to server: {e}")
                    sleep(5)
        
        # Start connection thread
        threading.Thread(target=connect_thread, daemon=True).start()

    def _accept_connections(self):
        """Thread for accepting new incoming connections.
        Ofc, in our case there is only one client but this should allow it to reconnect after losing connection"""
        while self.running:
            try:
                self.conn, addr = self.socket.accept()
                self.conn.settimeout(20)  # Set timeout for operations
                self.connected = True
                self.logger.info(f"Connection established with {addr}")
            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Error accepting connection: {e}")
                self.connected = False
                # Try to restart the server if it fails
                sleep(5)
                self._start_server()


    def _listener_worker(self):
        """Worker thread to listen for incoming messages"""
        while self.running:
            if not self.connected:
                sleep(1)
                continue
                
            try:
                # Check if there's data to read
                message_type, payload = self._receive_message()
                if message_type:
                    # self.logger.info(f"Added {message_type} to the queue")
                    self.receive_queue.put((message_type, payload))
            except socket.timeout:
                # This is expected with the timeout we set
                continue
            except ConnectionResetError:
                self.logger.warning("Connection reset by peer")
                self.connected = False
                self.receive_queue.put((MessageType.DISCONNECT, None))
                if not self.is_parent:
                    # Try to reconnect if we're the client
                    self._start_client()
            except Exception as e:
                self.logger.error(f"Error in listener worker: {e}")
                self.connected = False
                self.receive_queue.put((MessageType.ERROR, str(e)))
                
            sleep(2)  # Small sleep to prevent CPU hogging
            

    def _sender_worker(self):
        """Worker thread to send messages from queue"""
        while self.running:
            try:
                if not self.connected:
                    sleep(1)
                    continue
                    
                # Get message from queue with timeout
                try:
                    message_type, payload = self.send_queue.get(timeout=1)
                    self.logger.info(f"Sending message of type {message_type}")
                    self._send_message(message_type, payload)
                    self.send_queue.task_done()
                except queue.Empty:
                    # No messages to send
                    continue
            except Exception as e:
                self.logger.error(f"Error in sender worker: {e}")
                sleep(1)

    def _heartbeat_worker(self):
        """Worker thread to send periodic heartbeats"""
        while self.running:
            if self.connected:
                try:
                    self.send_message(MessageType.HEARTBEAT, None)
                except Exception as e:
                    self.logger.error(f"Error sending heartbeat: {e}")
            sleep(15)  # Send heartbeat every 15 seconds

    def _send_message(self, message_type, payload):
        """Low-level send message"""
        if not self.connected or not self.conn:
            return False

        try:
            # Format: [1 byte message type][4 bytes payload size][payload bytes]
            message_header = message_type.value.to_bytes(1, byteorder='big')

            if payload is None:
                # No payload, just send header with 0 size
                size_header = (0).to_bytes(4, byteorder='big')
                self.conn.sendall(message_header + size_header)
            else:
                # Serialize payload
                if message_type == MessageType.IMAGE_FRAMES:
                    # Serialize all frames at once instead of individual frames
                    serialised_payload = pickle.dumps(payload)  # payload is the list of frames
                    size_header = len(serialised_payload).to_bytes(4, byteorder='big')
                    self.conn.sendall(message_header + size_header + serialised_payload)
                    self.logger.debug(f"Frames sent, total size: {len(serialised_payload)}")
                    # for img in payload:
                        # img = cv2.imencode('.jpg', img)[1] # Compress image
                        # serialized_payload = pickle.dumps(img)
                        # size_header = len(serialized_payload).to_bytes(4, byteorder='big')
                        # self.logger.debug(f"Sending frame of size {len(serialized_payload)}")
                        # # self.conn.send(len(serialized_payload).to_bytes(8, byteorder='big'))
                        # self.conn.sendall(message_header + size_header + serialized_payload)
                        # self.logger.debug(f"Frame sent.")
                else:
                    serialized_payload = pickle.dumps(payload)
                    size_header = len(serialized_payload).to_bytes(4, byteorder='big')
                    self.conn.sendall(message_header + size_header + serialized_payload)
                    
            return True
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            self.connected = False
            return False

    def _receive_message(self):
        print("Receiving a message!")
        """Low-level receive message with additional debugging"""
        if not self.connected or not self.conn:
            return None, None
            
        try:
            # Read message type
            header = self.conn.recv(1)
            if not header:
                raise ConnectionResetError("Connection closed")
                
            # Convert byte to int and log it
            message_type_value = int.from_bytes(header, byteorder='big')
            self.logger.debug(f"Received message type value: {message_type_value}, raw bytes: {header.hex()}")
            
            # Check if the value is valid
            try:
                message_type = MessageType(message_type_value)
                self.logger.debug(f"Message type received: {message_type}")
            except ValueError:
                self.logger.error(f"Received invalid MessageType value: {message_type_value}")
                # Option 1: Skip this message and continue
                return None, None
                # Option 2 (alternative): Force a specific message type for debugging
                # message_type = MessageType.ERROR

            # Read payload size
            size_header = self.conn.recv(4)
            if not size_header:
                raise ConnectionResetError("Connection closed")
                
            payload_size = int.from_bytes(size_header, byteorder='big')
            
            # No payload
            if payload_size == 0:
                # self.logger.debug(f"Message of type {MessageType(message_type_value)} has no value.")
                return message_type, None
                
            # Read payload
            payload_data = bytearray()
            chunk_size = 65536  

            self.logger.debug(f"Expecting {payload_size} bytes for payload.")
            while len(payload_data) < payload_size and self.running:
                try:
                    remaining = payload_size - len(payload_data)
                    chunk = self.conn.recv(min(chunk_size, remaining))
                    if not chunk:
                        self.logger.error(f"Connection closed while reading payload. Read {len(payload_data)} bytes so far.")
                        raise ConnectionResetError("Connection closed during payload transfer")
                    payload_data += chunk

                    if (payload_size > 1024*1024) and (len(payload_data) % (1024*1024) == 0):
                        self.logger.debug(f"Received chunk: {len(chunk) / (1024*1024):.1f} MB. Total so far: {len(payload_data) / (1024*1024):.1f}/{payload_size / (1024*1024):.1f} MB")

                    self.logger.debug(f"Received chunk: {len(chunk)} bytes. Total so far: {len(payload_data)}/{payload_size}")       

                except socket.timeout:
                    self.logger.error(f"Timeout while receiving payload ({len(payload_data)}/{payload_size} bytes)")
                    continue #continue trying to receive more data
            # payload_data = b""
            # self.logger.debug(f"Reading the payload of message with type {MessageType(message_type_value)}.")
            # while len(payload_data) < payload_size:
            #     chunk = self.conn.recv(min(4096, payload_size - len(payload_data)))
            #     if not chunk:
            #         raise ConnectionResetError("Connection closed during payload transfer")
            #     payload_data += chunk
            
            # self.logger.debug(f"Payload of message with type {MessageType(message_type_value)} read successfully.")
            
            # Deserialize payload
            try:
                payload = pickle.loads(payload_data)
                # self.logger.debug(f"Payload deserialized successfully: {type(payload)}")
                return message_type, payload

            except pickle.UnpicklingError as e:
                self.logger.error(f"Failed to deserialize payload: {e}")
                return message_type, None
                        
        except socket.timeout:
            # This is expected with the timeout we set
            self.logger.debug(f"Message of type {MessageType(message_type_value)} caused a timeout!")
            return None, None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            self.connected = False
            raise

    def send_message(self, message_type, payload):
        """Add message to send queue"""
        self.send_queue.put((message_type, payload))

    def get_message(self, block=True, timeout=None):
        """Get message from receive queue"""
        try:
            return self.receive_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None, None

    def process_messages(self, callback):
        """Process messages with callback function
        
        callback should be a function that takes (message_type, payload)
        and returns True if message was handled
        """
        while not self.receive_queue.empty():
            message_type, payload = self.receive_queue.get()
            handled = callback(message_type, payload)
            self.receive_queue.task_done()
            if not handled:
                self.logger.warning(f"Unhandled message type: {message_type}")

    # Higher-level message functions
    def request_capture(self):
        """Request client to capture images"""
        self.send_message(MessageType.CAPTURE_REQUEST, None)
        self.logger.info("Capture request sent")

    def send_image_frames(self, frames):
        """Send image frames"""
        self.send_message(MessageType.IMAGE_FRAMES, frames)
        self.logger.info(f"Sending {len(frames)} frames")

    def send_object_detection_results(self, objects):
        """Send object detection results"""
        self.send_message(MessageType.OBJECT_DETECTION, objects)
        self.logger.info(f"Sending object detection data for {len(objects)} objects")

    def is_connected(self):
        """Check if connected"""
        return self.connected


if __name__ == "__main__":
    choices = {'client': 0, 'server': 1}
    parser = argparse.ArgumentParser(description='Send and receive over TCP')
    parser.add_argument('role', choices=choices, help='which role to play')
    args = parser.parse_args()

    print(args.role)
    is_parent = choices[args.role]

    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} - {levelname} - {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler("commshandler.log"),
            logging.StreamHandler()
        ]
    )

    # print(HOST)

    if is_parent == 0:
        remote_host = socket.gethostbyname("DESKTOP-BBMI8DR") # remote host is the server's IP.
        CommsHandlerInstance = CommsHandler(is_parent, HOST, PORT, remote_host)

        CommsHandlerInstance.start()
        print(type(CommsHandlerInstance.conn))
    else:
        print("Setting up parent instance...")
        CommsHandlerInstance = CommsHandler(is_parent, HOST, PORT)
        CommsHandlerInstance.start()
    

    while CommsHandlerInstance.is_connected:
        sleep(0.5)
        if input():
            break
    
    CommsHandlerInstance.stop()
