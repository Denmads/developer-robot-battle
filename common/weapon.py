from dataclasses import dataclass, field
from datetime import timedelta
from enum import IntEnum
import math


@dataclass
class Weapon:
    id: str
    x: float
    y: float
    angle: float
    type: "WeaponType"
    stats: "WeaponStats"
    
    cooldown_time_left: float = field(default=0, init=False)

class WeaponType(IntEnum):
    STANDARD = 1,
    CANNON = 2,
    SNIPER = 3,
    MINE_DEPLOYER = 4

@dataclass
class WeaponConfig:
    id: str
    x: float
    y: float
    angle: float
    type: WeaponType = field(default=WeaponType.STANDARD)
    
    def normalized_x(self) -> float:
        length = math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
        return self.x / length if length > 1 else self.x
    
    def normalized_y(self) -> float:
        length = math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
        return self.y / length if length > 1 else self.y
    
@dataclass
class WeaponStats:
    base_energy_cost: float
    consecutive_energy_cost_factor: float
    cooldown_seconds: float
    base_damage: float
    bullet_size: int
    bullet_speed: float
    projectile_life_time: timedelta | None = field(default=None)
    
STANDARD_WEAPON_STATS = WeaponStats(
    base_energy_cost=5,
    consecutive_energy_cost_factor=1.20,
    cooldown_seconds=0.5,
    base_damage=3,
    bullet_size=5,
    bullet_speed=6.66
)

CANNON_WEAPON_STATS = WeaponStats(
    base_energy_cost=20,
    consecutive_energy_cost_factor=1.10,
    cooldown_seconds=3,
    base_damage=15,
    bullet_size=10,
    bullet_speed=3
)

SNIPER_WEAPON_STATS = WeaponStats(
    base_energy_cost=10,
    consecutive_energy_cost_factor=1.10,
    cooldown_seconds=2,
    base_damage=8,
    bullet_size=3,
    bullet_speed=25
)

MINE_DEPLOYER_WEAPON_STATS =  WeaponStats(
    base_energy_cost=10,
    consecutive_energy_cost_factor=1.10,
    cooldown_seconds=2,
    base_damage=15,
    bullet_size=8,
    bullet_speed=0,
    projectile_life_time=timedelta(seconds=5)
)

def get_weapon_stats(type: WeaponType) -> WeaponStats:
    if type == WeaponType.STANDARD:
        return STANDARD_WEAPON_STATS
    elif type == WeaponType.CANNON:
        return CANNON_WEAPON_STATS
    elif type == WeaponType.SNIPER:
        return SNIPER_WEAPON_STATS
    elif type == WeaponType.MINE_DEPLOYER:
        return MINE_DEPLOYER_WEAPON_STATS
    