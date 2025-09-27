from dataclasses import dataclass
import random
import colorsys

class PlayerColors:
    colors: dict[int, tuple[int, int, int]]
    
    def __init__(self, ids: list[int]):
        self.colors = {}
        for id in ids:
            h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
            self.colors[id] = [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]


class GameState:
    players: list["PlayerState"]
    projectiles: list["ProjectileState"]

@dataclass
class PlayerState:
    idx: int
    x: int
    y: int
    angle: float
    hp: int
    
@dataclass
class ProjectileState:
    x: int
    y: int
    angle: float
    size: int