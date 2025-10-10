from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

import pygame

from client.core.tcp_client import TCPClient
from common.robot import Robot


class ClientState(Enum):
    NOT_CONNECTED = 1
    IN_LOBBY = 2
    IN_GAME = 3
    IN_TEST = 4

@dataclass
class SharedState:
    path: str
    player_id: str
    menu_size: tuple[int, int]
    client_state: ClientState
    tcp: TCPClient
    udp_port: int
    
    robot: Robot = field(default=None, init=False)
    font_header: pygame.font.Font
    font_text: pygame.font.Font

class StateRenderer:
    
    def __init__(self, shared_state: SharedState):
        self.state = shared_state
    
    def render(self, screen: pygame.Surface, delta: timedelta):
        pass
    
    def on_event(self, event: pygame.event.Event):
        pass