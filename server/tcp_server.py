import dataclasses
import json
import socket
import threading
from typing import Callable
from common import tcp_messages as tm
class TCPServer:
    def __init__(self, input_callback: Callable[[tm.InputMessage], None], host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = False

        self.id_counter = 1

        self.input_callback = input_callback

    def start(self):
        print(f"Server listening on {self.host}:{self.port}")
        self.running = True
        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.daemon = True
            thread.start()

    def handle_client(self, client_socket: socket.socket):
        with client_socket:
            client_socket.sendall(json.dumps(dataclasses.asdict(tm.PlayerInfo(self.id_counter))).encode())
            self.id_counter += 1

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode().strip())
                self.input_callback(tm.InputMessage(**message))

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("Server stopped.")