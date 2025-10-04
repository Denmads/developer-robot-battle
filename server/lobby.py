import dataclasses
import datetime
import json
import threading
from typing import Callable

from common.arena import Arena
from common.robot import RobotInterface
from common.tcp_messages import LobbyInfoMessage, LobbyJoinedMessage, RoundEndedMessage, RoundStartedMessage
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
        player.sender.send(LobbyJoinedMessage())
            
    def remove_player(self, player: Player, send_update: bool = True):
        self.players.remove(player)
        if send_update:
            self._send_lobby_update()
            
        if self.game is not None:
            self.game.remove_disconnected_player(player)
        
    def _send_lobby_update(self):
        message = LobbyInfoMessage({p.id: p.color for p in self.players})
        for player in self.players:
            player.sender.send(message)
            
    def is_started(self) -> bool:
        return self.game is not None
    
    def start(self, is_test: bool):
        arena = Arena.create(len(self.players))
        
        start_time = datetime.datetime.now() 
        if not is_test:
            start_time += datetime.timedelta(0, 3)
        message = RoundStartedMessage(
            start_time.isoformat(),
            arena.width,
            arena.height)
        for player in self.players:
            player.sender.send(message)

        self.game = Game(
            self.players, 
            arena,
            self.udp_socket.send_to_all, 
            self._on_game_ended, 
            start_time, 
            is_test)
        threading.Thread(target=self.game.run, daemon=True).start()
        
    def stop(self):
        self.game.stop()
        
    def _on_game_ended(self, winner_idx: int):
        winner = self.players[winner_idx]
        message = RoundEndedMessage(winner.id)
        for player in self.players:
            player.sender.send(message)        
        
        # self._send_lobby_update()
        self.game = None
        self.game_ended()