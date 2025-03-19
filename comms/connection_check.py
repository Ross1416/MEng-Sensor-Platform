import requests
import socket

def check_connection(remote="www.google.com", port=80, timeout=3):
    try:
        with socket.create_connection((remote, port), timeout) as sock:
            return True
    except socket.error as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    if check_connection():
        print("The Internet is connected.")
    else:
        print("The Internet is not connected.")

    if check_connection("192.168.1.59"):
        print("The Pi is connected.")
    else:
        print("The Pi is not connected.")