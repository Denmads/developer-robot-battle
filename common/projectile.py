from dataclasses import dataclass, field


@dataclass
class Projectile:
    id: int
    owner_idx: str
    x: int
    y: int
    angle: float
    size: int
    speed: float
    damage: int
    
    destroy: bool = field(default=False, init=False)