import dataclasses
import json
import socket

from common.tcp_messages import Message


class TcpSender:
    
    def __init__(self, socket: socket.socket):
        self.socket = socket
        
    def send(self, message: Message):
        message_as_dict = json.dumps(dataclasses.asdict(message))
        
        message_bytes = bytearray(message_as_dict.encode())
        message_bytes.insert(0, 2)
        message_bytes.insert(len(message_bytes), 3)
        
        self.socket.sendall(message_bytes)