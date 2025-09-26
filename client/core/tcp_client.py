import dataclasses
import json
import socket

class TCPClient:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

    def send(self, message: object):
        self.client_socket.sendall(json.dumps(dataclasses.asdict(message)).encode())

    def close(self):
        self.client_socket.close()
        print("Connection closed.")