import dataclasses
import json
import socket
import threading

from common.tcp_messages import PlayerInfoMessage, RobotClassMessage

class TCPClient:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")
        thread = threading.Thread(target=self.listen)
        thread.daemon = True
        thread.start()

    def listen(self):
        with self.client_socket:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode().strip())
                info = PlayerInfoMessage(**message)
                with open("my_robot.py") as f:
                    self.send(RobotClassMessage(info.id, f.read()))

    def send(self, message: object):
        self.client_socket.sendall(json.dumps(dataclasses.asdict(message)).encode())

    def close(self):
        self.client_socket.close()
        print("Connection closed.")