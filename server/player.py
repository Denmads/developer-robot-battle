import socket
from dataclasses import dataclass
from common.robot import RobotInterface

@dataclass
class Player:
    id: str
    udp_port: int
    socket: socket.socket
    robot: RobotInterface
    