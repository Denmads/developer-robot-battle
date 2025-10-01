import dataclasses
import datetime
import json
import logging
import socket
import threading
from typing import Callable

from common.tcp_messages import LobbyInfoMessage, LobbyJoinedMessage, Message, RoundEndedMessage, RoundStartedMessage

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
            buffer = bytearray()
            while self.connected:
                data = self.client_socket.recv(1024)
                if not data:
                    self.close()
                    self.disconnect_callback()
                    break
                
                buffer += data

                while self._buffer_has_full_message(buffer):
                    self._handle_message_in_buffer(buffer)
        except:
            self.close()
            self.disconnect_callback()
    
    def _buffer_has_full_message(self, buffer: bytearray) -> bool:
        return buffer.find(2) != -1 and buffer.find(3) != -1

    def _handle_message_in_buffer(self, buffer: bytearray):
        try:
            stx_index = buffer.find(2)
            etx_index = buffer.find(3)
            
            data = buffer[stx_index+1:etx_index]
            del buffer[:etx_index+1]
            
            message_data = data.decode().strip()
            message = json.loads(message_data)
            self.message_callback(self.parse_message(message))
        except Exception as ex:
            print(f"Unabled to parse message: {data.decode().strip()}")
            logger = logging.getLogger(__name__)
            logger.exception(ex)
    
                
    def parse_message(self, message):
        message_type = message["message_type"]
        del message["message_type"]
        
        if message_type == 4:
            return LobbyInfoMessage(**message)
        elif message_type == 6:
            return RoundStartedMessage(**message)
        elif message_type == 7:
            return RoundEndedMessage(**message)
        elif message_type == 8:
            return LobbyJoinedMessage(**message)

    def send(self, message: object):
        message_bytes = bytearray(json.dumps(dataclasses.asdict(message)).encode())
        message_bytes.insert(0, 2)
        message_bytes.insert(len(message_bytes), 3)
        self.client_socket.sendall(message_bytes)

    def close(self):
        self.connected = False
        self.client_socket.close()
        print("Connection closed.")