import json
import socket
import threading
import traceback
from typing import Callable
from common import tcp_messages as tm
import re
import logging

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
            buffer: bytes = bytearray()
            while True:
                data = client_socket.recv(1024)
                if not data:
                    self.disconnect_callback(client_socket)
                    break

                buffer += data

                while self._buffer_has_full_message(buffer):
                    self._handle_message_in_buffer(client_socket, buffer)

        except:
            self.disconnect_callback(client_socket)

    def _buffer_has_full_message(self, buffer: bytearray) -> bool:
        return buffer.find(2) != -1 and buffer.find(3) != -1

    def _handle_message_in_buffer(self, socket: socket.socket, buffer: bytearray):
        try:
            stx_index = buffer.find(2)
            etx_index = buffer.find(3)
            
            data = buffer[stx_index+1:etx_index]
            del buffer[:etx_index+1]
            
            message_data = data.decode().strip()
            message = json.loads(message_data)
            self.message_callback(socket, self.parse_message(message))
        except Exception as ex:
            print(f"Unabled to parse message: {data.decode().strip()}")
            logger = logging.getLogger(__name__)
            logger.exception(ex)

    def parse_message(self, message):
        message_type = message["message_type"]
        del message["message_type"]
        
        if message_type == 1:
            return tm.InputMessage(**message)
        elif message_type == 2:
            return tm.PlayerInfoMessage(**message)
        elif message_type == 3:
            return tm.StartRoundMessage(**message)
        elif message_type == 5:
            return tm.ExitTestMessage()

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("Server stopped.")