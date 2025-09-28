import pickle
import socket
import struct

from common.constants import MAX_UDP_PACKET_SIZE
from common.udp_message import UDPMessage
from server.player import Player


class UDPSocket:
    
    def __init__(self, player_dict: dict[socket.socket, Player]):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.players = player_dict
        
        self.message_id_counter = 0
        
    def send_to_all(self, data: UDPMessage):
        packets = self._split_into_packets(data)
        
        for player in self.players.values():
            ip, _ = player.socket.getpeername()
            for packet in packets:
                self.socket.sendto(packet, (ip, player.udp_port))
            
    def _split_into_packets(self, data: UDPMessage) -> list[bytes]:
        full_byte_data = data.to_bytes()
        
        chunks = [
            full_byte_data[i:i+MAX_UDP_PACKET_SIZE]
            for i in range(0, len(full_byte_data), MAX_UDP_PACKET_SIZE)
        ]
        
        packets = []
        for i, chunk in enumerate(chunks):
            header = struct.pack("<HHHH", self.message_id_counter, data.message_type, i, len(chunks))
            packets.append(header + b"||" + chunk)
            
        self.message_id_counter = (self.message_id_counter + 1) % 65000
        return packets