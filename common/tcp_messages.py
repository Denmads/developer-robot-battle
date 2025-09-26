from dataclasses import dataclass, field


@dataclass
class InputMessage:
    message_type: int = field(default=1, init=False)
    player_id: int
    key: int
    state: int

@dataclass
class RobotClassMessage:
    message_type: int = field(default=2, init=False)
    player_id: int
    code: str

@dataclass
class PlayerInfoMessage:
    message_type: int = field(default=3, init=False)
    id: int