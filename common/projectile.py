from dataclasses import dataclass, field
from enum import IntEnum
import math

from common.arena import Arena
from common.player_instance import PlayerInstance

class ProjectileModifier(IntEnum):
    HOMING = 1,
    EXPLOSIVE = 2,
    PIERCING = 4,
    BOUNCING = 8
    
@dataclass
class ProjectileModifierStats:
    energy_cost_multiplier: float

    def update(self, projectile: "Projectile", alive_players: list[PlayerInstance], arena: Arena):
        pass

    def on_player_hit(self, projectile: "Projectile", player: PlayerInstance) -> bool:
        """Returns True if default hit behaviour should be skipped"""
        return False
    
@dataclass
class HomingProjectileModifierStats(ProjectileModifierStats):
    max_steering_per_tick: float
    max_tracking_dist: float

    def update(self, projectile: "Projectile", alive_players: list[PlayerInstance], arena: Arena):
        max_tracking_dist_squared = self.max_tracking_dist * self.max_tracking_dist
            
        closest_player: PlayerInstance = None
        closest_dist: float = math.inf
        for player in alive_players:
            if player.idx == projectile.owner_idx:
                continue
                
            x_diff = projectile.x - player.robot.x 
            y_diff = projectile.y - player.robot.y
            dist = x_diff * x_diff + y_diff * y_diff
            if dist <=  max_tracking_dist_squared and dist < closest_dist:
                closest_player = player
                closest_dist = dist
                    
        if closest_player is not None:
            x_diff = player.robot.x  - projectile.x
            y_diff = player.robot.y - projectile.y
            
            projectile_angle = math.atan2(projectile.velocity[1], projectile.velocity[0])
            angle_to_player = math.atan2(y_diff, x_diff)

            angle_diff = angle_to_player - projectile_angle
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            angle_diff_clamped = min(max(-self.max_steering_per_tick, angle_diff), self.max_steering_per_tick)

            new_angle = projectile_angle + angle_diff_clamped
            projectile.velocity = (
                math.cos(new_angle),
                math.sin(new_angle)
            )
    
@dataclass
class ExplosiveProjectileModifierStats(ProjectileModifierStats):
    explosion_radius: int
    
@dataclass
class PiercingProjectileModifierStats(ProjectileModifierStats):
    max_piercings: int
    piercings: int = field(default=0, init=False)

    hit_players: list[int] = field(default_factory=list, init=False)

    def update(self, projectile: "Projectile", alive_players: list[PlayerInstance], arena: Arena):
        for player in filter(lambda p: p.idx in self.hit_players , alive_players):
            dist = math.pow(player.robot.x - projectile.x, 2) + math.pow(player.robot.y - projectile.y, 2)
            if dist > player.robot.size * player.robot.size:
                self.hit_players.remove(player.idx)

    def on_player_hit(self, projectile: "Projectile", player: PlayerInstance):
        projectile.destroy = self.piercings - 1 == self.max_piercings
        if self.piercings < self.max_piercings and player.idx not in self.hit_players:
            player.robot.hp -= projectile.damage
            self.hit_players.append(player.idx)
            self.piercings += 1

        return True
    
@dataclass
class BouncingProjectileModifierStats(ProjectileModifierStats):
    max_bounces: int
    bounces: int = field(default=0, init=False)

    def update(self, projectile: "Projectile", alive_players: list[PlayerInstance], arena: Arena):
        if self.bounces < self.max_bounces:
            if self._is_touching_screen_border_y(projectile, arena):
                self.bounces += 1
                projectile.velocity = self._reflect_projectile(projectile, 0)
                
        if self.bounces < self.max_bounces:
            if self._is_touching_screen_border_x(projectile, arena):
                self.bounces += 1
                projectile.velocity = self._reflect_projectile(projectile, math.pi / 2)
                
    def _reflect_projectile(self, projectile: "Projectile", wall_angle: float):
        nx = -math.sin(wall_angle)
        ny = math.cos(wall_angle)
        
        dot = projectile.velocity[0] * nx + projectile.velocity[1] * ny
        
        return (
            projectile.velocity[0] - 2 * dot * nx,
            projectile.velocity[1] - 2 * dot * ny
        )
                
      
    def _is_touching_screen_border_x(self, projectile: "Projectile", arena: Arena):
        return projectile.x < projectile.size or projectile.x > arena.width - projectile.size
    
    def _is_touching_screen_border_y(self, projectile: "Projectile", arena: Arena):
        return projectile.y < projectile.size or projectile.y > arena.height - projectile.size
    

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
    
    destroy: bool = field(default=False, init=False)