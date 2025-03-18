import requests
import socket

def check_connection(remote="www.google.com", port=80, timeout=3):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((remote, port))
        return True
    except socket.error:
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    if check_connection():
        print("The Internet is connected.")
    else:
        print("The Internet is not connected.")

    if check_connection("192.168.1.59"):
        print("The Pi is connected.")
    else:
        print("The Pi is not connected.")