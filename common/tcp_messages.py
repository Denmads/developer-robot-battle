from dataclasses import dataclass, field

class Message:
    pass

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
class StartMessage(Message):
    message_type: int = field(default=3, init=False)