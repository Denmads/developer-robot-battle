import pickle
import socket

from server.player import Player


class UDPSocket:
    
    def __init__(self, player_dict: dict[socket.socket, Player]):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.players = player_dict
        
    def send_to_all(self, data: object):
        data = pickle.dumps(data)
        
        for player in self.players.values():
            ip, _ = player.socket.getpeername()
            self.socket.sendto(data, (ip, player.udp_port))