import pickle
import socket
import threading
from time import sleep
from common.constants import UDP_PORT
from common.game_state import GameState, PlayerColors
from common.robot import RobotInterface
from common.tcp_messages import InputMessage, Message, PlayerInfoMessage, StartMessage
from server.game import Game
from server.player import Player
from server.tcp_server import TCPServer


class GameServer:
    def __init__(self, port: int = 5000):
        self.tcpServer = TCPServer(self._on_message, port=port)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.players: list[Player] = []
        self.game: Game = None
        
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
            self.players.append(Player(message.id, message.udp_port, socket, robot))
        elif isinstance(message, InputMessage):
            self.game.update_key(message.player_id, message.key, message.state)
        elif isinstance(message, StartMessage):
            if self.game is None:
                print("Starting...", flush=True)
                self._send_udp(PlayerColors([idx for idx, _ in enumerate(self.players)]))
                self.game = Game(self.players, self._send_state)
                threading.Thread(target=self.game.run, daemon=True).start()
            
    def _parse_robot(self, robot_code: str) -> RobotInterface:
        namespace = {}
        exec(robot_code, namespace)

        # Get the class reference from the namespace
        MyRobot = namespace["MyRobot"]

        # Create an instance
        return MyRobot()
    
    def _send_state(self, state: GameState):
        self._send_udp(state)
            
    def _send_udp(self, data: object):
        data = pickle.dumps(data)
        
        for player in self.players:
            ip, _ = player.socket.getpeername()
            self.udp_socket.sendto(data, (ip, player.udp_port))