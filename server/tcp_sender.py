import dataclasses
import json
import socket

from common.tcp_messages import Message


class TcpSender:
    
    def __init__(self, socket: socket.socket):
        self.socket = socket
        
    def send(self, message: Message):
        message_as_dict = json.dumps(dataclasses.asdict(message))
        self.socket.sendall(message_as_dict.encode())