from dataclasses import dataclass, field
import random
import colorsys
import struct

from common.robot_hull import RobotHullType



class UDPMessage:
    
    def __init__(self, message_type: int):
        self.message_type = message_type
        
    def to_bytes(self) -> bytes:
        pass
    
    @staticmethod
    def from_bytes(data: bytes) -> "UDPMessage":
        pass

class PlayerStaticInfoMessage(UDPMessage):
    player_info: list["PlayerStaticInfo"]
    
    def __init__(self):
        super().__init__(1)
            
    def to_bytes(self) -> bytes:
        buf = bytearray()
        buf += struct.pack("<H", len(self.player_info))
        
        for p in self.player_info:
            buf += struct.pack(PlayerStaticInfo.struct_format, p.idx, p.color[0], p.color[1], p.color[2], p.hull, p.size, p.max_hp, p.max_energy)
            
        return bytes(buf)
    
    @staticmethod
    def from_bytes(data: bytes) -> UDPMessage:
        offset = 0
        num_players, = struct.unpack_from("<H", data, offset)
        offset += 2
        
        info = PlayerStaticInfoMessage()
        info.player_info = []
        for _ in range(num_players):
            idx, r, g, b, hull, size, max_hp, max_energy \
                = struct.unpack_from(PlayerStaticInfo.struct_format, data, offset)
            info.player_info.append(PlayerStaticInfo(idx, (r, g, b), hull, size, max_hp, max_energy))
            offset += struct.calcsize(PlayerStaticInfo.struct_format)
        
        return info

@dataclass
class PlayerStaticInfo:
    struct_format: str = field(default="<HHHHHHHH", init=False)
    
    idx: int
    color: tuple[int, int, int]
    hull: RobotHullType
    size: int
    max_hp: int
    max_energy: int


class GameStateMessage(UDPMessage):
    players: list["PlayerState"]
    projectiles: list["ProjectileState"]
    
    def __init__(self):
        super().__init__(2)
    
    def to_bytes(self) -> bytes:
        buf = bytearray()
        buf += struct.pack("<HH", len(self.players), len(self.projectiles))
        
        for p in self.players:
            buf += struct.pack(PlayerState.struct_format, p.idx, p.x, p.y, p.angle, p.hp, p.energy)
        for p in self.projectiles:
            buf += struct.pack(ProjectileState.struct_format, p.x, p.y, p.angle, p.size)
            
        return bytes(buf)
    
    @staticmethod
    def from_bytes(data: bytes) -> UDPMessage:
        offset = 0
        num_players, num_projectiles = struct.unpack_from("<HH", data, offset)
        offset += 4
        
        state = GameStateMessage()
        state.players = []
        for _ in range(num_players):
            vals = struct.unpack_from(PlayerState.struct_format, data, offset)
            state.players.append(PlayerState(*vals))
            offset += struct.calcsize(PlayerState.struct_format)
            
        state.projectiles = []
        for _ in range(num_projectiles):
            vals = struct.unpack_from(ProjectileState.struct_format, data, offset)
            state.projectiles.append(ProjectileState(*vals))
            offset += struct.calcsize(ProjectileState.struct_format)
        
        return state
    

@dataclass
class PlayerState:
    struct_format: str = field(default="<HhhfHH", init=False)
    
    idx: int
    x: int
    y: int
    angle: float
    hp: int
    energy: int
    
    
@dataclass
class ProjectileState:
    struct_format: str = field(default="<hhfH", init=False)
    
    x: int
    y: int
    angle: float
    size: int