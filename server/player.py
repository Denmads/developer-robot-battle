import colorsys
import random
import socket
from dataclasses import dataclass, field
from common.robot import RobotInterface

def get_random_color():
    h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
    return [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]


@dataclass
class Player:
    id: str
    udp_port: int
    socket: socket.socket
    robot_configuration: RobotInterface
    
    color: tuple[int, int, int] = field(default_factory=get_random_color, init=False)
    
