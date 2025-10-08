from collections import defaultdict
import socket
import struct
import threading
from typing import Callable

from common.constants import MAX_UDP_PACKET_SIZE
from common.udp_message import GameStateMessage, PlayerStaticInfoMessage, RobotStateMessage, UDPMessage


class UDPClient:
    
    def __init__(self, port: int, on_message_callback: Callable[[UDPMessage], None]):
        self.on_message_callback = on_message_callback
        
        self.buffers = defaultdict(lambda: {"parts": {}, "count": None})
        
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", int(port)))
        threading.Thread(target=self._udp_listener, daemon=True).start()
        
    def _udp_listener(self):
        while True:
            data, _ = self.udp_socket.recvfrom(MAX_UDP_PACKET_SIZE * 2)
            
            if len(data) < 8:
                continue
            
            header_raw, chunk = data.split(b"||", 1)
            msg_id, msg_type, part_idx, part_count =  struct.unpack_from("<HHHH", header_raw, 0)
            
            buf = self.buffers[msg_id]
            buf["parts"][part_idx] = chunk
            buf["count"] = part_count
            
            if len(buf["parts"]) == part_count:
                full = b"".join(buf["parts"][i] for i in range(part_count))
                del self.buffers[msg_id]
                
                message: UDPMessage = None
                if msg_type == 1:
                    message = PlayerStaticInfoMessage.from_bytes(full)
                elif msg_type == 2:
                    message = GameStateMessage.from_bytes(full)
                elif msg_type == 3:
                    message = RobotStateMessage.from_bytes(full)
            
                self.on_message_callback(message)
                
    def close(self):
        self.udp_socket.close()