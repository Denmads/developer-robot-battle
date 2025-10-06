from dataclasses import dataclass, field
from enum import IntEnum
import math

class ProjectileModifier(IntEnum):
    HOMING = 1,
    EXPLOSIVE = 2,
    PIERCING = 3,
    BOUNCING = 4
    
@dataclass
class ProjectileModifierStats:
    energy_cost_multiplier: float
    
@dataclass
class HomingProjectileModifierStats(ProjectileModifierStats):
    max_steering_per_tick: float
    max_tracking_dist: float
    
@dataclass
class ExplosiveProjectileModifierStats(ProjectileModifierStats):
    explosion_radius: int
    
@dataclass
class PiercingProjectileModifierStats(ProjectileModifierStats):
    max_piercings: int
    piercings: int = field(default=0, init=False)
    
@dataclass
class BouncingProjectileModifierStats(ProjectileModifierStats):
    max_bounces: int
    bounces: int = field(default=0, init=False)

def get_projectile_modifier_stats(modifier: ProjectileModifier) -> ProjectileModifierStats:
    if modifier == ProjectileModifier.HOMING:
        return HomingProjectileModifierStats(
            energy_cost_multiplier=1.3,
            max_steering_per_tick= 2 * (math.pi / 180),
            max_tracking_dist=150
        )
    elif modifier == ProjectileModifier.EXPLOSIVE:
        return ExplosiveProjectileModifierStats(
            energy_cost_multiplier=1.3,
            explosion_radius=80
        )
    elif modifier == ProjectileModifier.PIERCING:
        return PiercingProjectileModifierStats(
            energy_cost_multiplier=1.2,
            max_piercings=1
        )
    elif modifier == ProjectileModifier.BOUNCING:
        return BouncingProjectileModifierStats(
            energy_cost_multiplier=1.2,
            max_bounces=2
        )


@dataclass
class Projectile:
    id: int
    owner_idx: str
    x: int
    y: int
    velocity: tuple[float, float]
    size: int
    speed: float
    damage: int
    
    modifiers: dict[ProjectileModifier, ProjectileModifierStats]
    
    hit_players: list[int] = field(default_factory=list, init=False)
    
    destroy: bool = field(default=False, init=False)