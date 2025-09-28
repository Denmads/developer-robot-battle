from enum import Enum
import pickle
import socket
import threading
from time import sleep
from common.udp_message import GameStateMessage
from common.robot import RobotInterface
from common.tcp_messages import ExitTestMessage, InputMessage, Message, PlayerInfoMessage, StartMessage
from server.game import Game
from server.lobby import Lobby
from server.player import Player
from server.tcp_server import TCPServer
from server.udp_socket import UDPSocket


class ServerState(Enum):
    IN_LOBBY = 1
    IN_GAME = 2
    IN_TEST = 3

class GameServer:
    def __init__(self, port: int = 5000):
        self.socket_player_dict: dict[socket.socket, Player] = {}
        
        self.tcpServer = TCPServer(self._on_message, self._on_player_disconnect, port=port)
        self.udp_socket = UDPSocket(self.socket_player_dict)
        
        self.state: ServerState = ServerState.IN_LOBBY
        self.lobby = Lobby(self.udp_socket, self._on_game_ended)
        
    def start(self):
        threading.Thread(target=self.tcpServer.start, daemon=True).start()
        
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            self.tcpServer.stop()
        
    def _on_message(self, socket: socket.socket, message: Message):
        if isinstance(message, PlayerInfoMessage):
            print(f"Player connected '{message.id}'", flush=True)
            robot = self._parse_robot(message.robot_code)
            player = Player(message.id, message.udp_port, socket, robot)
            self.socket_player_dict[socket] = player
            self.lobby.add_player(player)
            
        elif isinstance(message, StartMessage):
            if not self.lobby.is_started():
                print("Starting...", flush=True)
                self.tcpServer.stop() # stops accepting new connections
                self.lobby.start(message.is_test)
                self.state = ServerState.IN_TEST if message.is_test else ServerState.IN_GAME
                
        elif isinstance(message, ExitTestMessage):
            if self.lobby.is_started():
                self.lobby.stop()
                
        elif isinstance(message, InputMessage):
            if self.lobby.is_started():
                self.lobby.game.update_key(message.player_id, message.key, message.state)
            
    def _parse_robot(self, robot_code: str) -> RobotInterface:
        namespace = {}
        exec(robot_code, namespace)

        # Get the class reference from the namespace
        MyRobot = namespace["MyRobot"]

        # Create an instance
        return MyRobot()
    
    
    def _on_player_disconnect(self, socket: socket.socket):
        player = self.socket_player_dict[socket]
        print(f"Player disconnected '{player.id}'")
        self.lobby.remove_player(player, send_update=self.state == ServerState.IN_LOBBY)
        
    def _on_game_ended(self):
        print("Game Ended")
        self.state = ServerState.IN_LOBBY
        threading.Thread(target=self.tcpServer.start, daemon=True).start()