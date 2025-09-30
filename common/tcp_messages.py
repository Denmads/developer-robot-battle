from dataclasses import dataclass, field
import datetime

class Message:
    pass


# Client -> Server
@dataclass
class InputMessage(Message):
    message_type: int = field(default=1, init=False)
    player_id: str
    key: int
    state: int

@dataclass
class PlayerInfoMessage(Message):
    message_type: int = field(default=2, init=False)
    id: str
    udp_port: int
    robot_code: str
    
@dataclass
class StartRoundMessage(Message):
    message_type: int = field(default=3, init=False)
    is_test: bool = field(default=False)
    
@dataclass
class ExitTestMessage(Message):
    message_type: int = field(default=5, init=False)

@dataclass
class RoundStartedMessage(Message):
    message_type: int = field(default=6, init=False)
    begin_time: str

    
    
# Server -> Client
@dataclass
class LobbyInfoMessage(Message):
    message_type: int = field(default=4, init=False)
    players: dict[str, tuple[int, int, int]]