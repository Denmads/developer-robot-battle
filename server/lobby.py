import dataclasses
import json
import threading
from typing import Callable

from common.robot import RobotInterface
from common.tcp_messages import LobbyInfoMessage
from server.game import Game
from server.player import Player
from server.udp_socket import UDPSocket


class Lobby:
    
    def __init__(self, upd_socket: UDPSocket, game_ended: Callable[[], None]):
        self.udp_socket = upd_socket
        self.game_ended = game_ended
        
        self.players: list[Player] = []
        
        self.game: Game = None
        
    def add_player(self, player: Player):
        self.players.append(player)
        self._send_lobby_update()
            
    def remove_player(self, player: Player, send_update: bool = True):
        self.players.remove(player)
        if send_update:
            self._send_lobby_update()
        
    def _send_lobby_update(self):
        message = LobbyInfoMessage([p.id for p in self.players])
        for player in self.players:
            player.socket.sendall(json.dumps(dataclasses.asdict(message)).encode())
            
    def is_started(self) -> bool:
        return self.game is not None
    
    def start(self, is_test: bool):
        self.game = Game(self.players, self.udp_socket.send_to_all, self._on_game_ended, is_test)
        threading.Thread(target=self.game.run, daemon=True).start()
        
    def stop(self):
        self._on_game_ended()
        
    def _on_game_ended(self):
        self._send_lobby_update()
        self.game = None
        self.game_ended()