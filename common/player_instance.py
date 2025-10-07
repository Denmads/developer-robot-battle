from dataclasses import dataclass, field

from common.player import Player
from common.robot import Robot


@dataclass
class PlayerKeyState:
    up: bool = field(init=False, default=False)
    down: bool = field(init=False, default=False)
    left: bool = field(init=False, default=False)
    right: bool = field(init=False, default=False)
    
    q: bool = field(init=False, default=False)
    w: bool = field(init=False, default=False)
    e: bool = field(init=False, default=False)
    a: bool = field(init=False, default=False)
    s: bool = field(init=False, default=False)
    d: bool = field(init=False, default=False)
    
    def clone(self) -> "PlayerKeyState":
        state = PlayerKeyState()
        
        state.up = self.up
        state.down = self.down
        state.left = self.left
        state.right = self.right
        
        state.q = self.q
        state.w = self.w
        state.e = self.e
        state.a = self.a
        state.s = self.s
        state.d = self.d
        
        return state

@dataclass
class PlayerInstance:
    idx: int
    player: Player
    robot: Robot
    dead: bool = field(default=False, init=False)
    
    # keys
    old_keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)
    keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)