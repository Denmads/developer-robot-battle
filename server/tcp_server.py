import json
import socket
import threading
from typing import Callable
from common import tcp_messages as tm
class TCPServer:
    def __init__(self, message_callback: Callable[[socket.socket, tm.Message], None], disconnect_callback: Callable[[socket.socket], None], host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.running = False

        self.message_callback = message_callback
        self.disconnect_callback = disconnect_callback

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        
        print(f"Server listening on {self.host}:{self.port}", flush=True)
        self.running = True
        
        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection from {addr}", flush=True)
                thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                thread.daemon = True
                thread.start()
        except:
            pass

    def handle_client(self, client_socket: socket.socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    self.disconnect_callback(client_socket)
                    break

                try:
                    message = json.loads(data.decode().strip())
                    self.message_callback(client_socket, self.parse_message(message))
                except:
                    print(f"Unabled to parse message: {data.decode().strip()}")
        except:
            self.disconnect_callback(client_socket)

    def parse_message(self, message):
        message_type = message["message_type"]
        del message["message_type"]
        
        if message_type == 1:
            return tm.InputMessage(**message)
        elif message_type == 2:
            return tm.PlayerInfoMessage(**message)
        elif message_type == 3:
            return tm.StartMessage(**message)
        elif message_type == 5:
            return tm.ExitTestMessage()

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("Server stopped.")