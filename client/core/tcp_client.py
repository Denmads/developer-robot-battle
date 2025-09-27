import dataclasses
import datetime
import json
import socket
import threading
from typing import Callable

from common.tcp_messages import LobbyInfoMessage, Message

class TCPClient:
    def __init__(self, message_callback: Callable[[Message], None], disconnect_callback: Callable[[], None], host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.message_callback = message_callback
        self.disconnect_callback = disconnect_callback
        
        self.connected = False

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")
        self.connected = True
        
        threading.Thread(target=self._listen, daemon=True).start()
        
    def _listen(self):
        try:
            while self.connected:
                data = self.client_socket.recv(1024)
                if not data:
                    self.close()
                    self.disconnect_callback()
                    break
                message = json.loads(data.decode().strip())
                self.message_callback(self.parse_message(message))
        except:
            self.close()
            self.disconnect_callback()
            
                
    def parse_message(self, message):
        message_type = message["message_type"]
        del message["message_type"]
        
        if message_type == 4:
            return LobbyInfoMessage(**message)

    def send(self, message: object):
        self.client_socket.sendall(json.dumps(dataclasses.asdict(message)).encode())

    def close(self):
        self.connected = False
        self.client_socket.close()
        print("Connection closed.")