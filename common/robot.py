from dataclasses import dataclass, field
import math
from typing import Callable

import pygame

from common.robot_hull import RobotHullType, get_hull_instance
from common.robot_stats import RobotStats
from common.weapon import Weapon, WeaponConfig, get_weapon_stats
from common.weapon_command import WeaponCommand

@dataclass
class RobotBuilder:
    hull: RobotHullType = field(default=RobotHullType.STANDARD)
    weapons: list[WeaponConfig] = field(default_factory=list)

@dataclass
class ProjectileInfo:
    x: float
    y: float
    velocity: tuple[float, float]
    speed: float

@dataclass
class RobotInfo:
    position: tuple[float, float]
    angle: float
    hp: float
    max_hp: float
    energy: float
    max_energy: float
    cooldowns: dict[str, float]
    enemies: list[tuple[float, float]]
    projectiles: list[ProjectileInfo]

class RobotInterface:
    
    def build_robot(self, builder: RobotBuilder) -> None:
        pass
    
    def apply_stats(self, stats: RobotStats) -> None:
        pass

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        pass
    
    def get_state(self, info: RobotInfo) -> dict:
        pass
    
    def draw_gui(self, screen: pygame.Surface, arena_size: tuple[int, int], state: dict) -> None:
        pass
    
def parse_robot_config_from_string(code: str) -> RobotInterface:
    namespace = {}
    exec(code, namespace)

    # Get the class reference from the namespace
    MyRobot = namespace["MyRobot"]

    # Create an instance
    return MyRobot()


class Robot:
    
    def __init__(self, interface: RobotInterface, configuration: RobotBuilder, stats: RobotStats, x: int, y: int, angle: float, ability_func: Callable[[int, list[WeaponCommand], RobotInfo], None]):
        self.interface = interface
        self.configuration = configuration
        self.hull = get_hull_instance(configuration.hull)
        
        self.stats = stats
        self.ability_func = ability_func
        
        self.x = x
        self.y = y
        self.angle = angle
        
        self.size = self.hull.size - max(round(self.stats.size), 5)
        
        self.max_hp = self.hull.max_health + round(self.stats.max_health * 5)
        self.hp = self.max_hp
        
        self.max_energy = self.hull.max_energy + round(self.stats.max_energy * 5)
        self.energy = self.max_energy
        self.energy_regen = self.hull.energy_regen + self.stats.energy_regen * 0.02
        
        self.move_speed = self.hull.move_speed + self.stats.move_speed * 0.5
        self.turn_speed = self.hull.turn_speed + self.stats.turn_speed * 0.02
        
        self.weapons = Robot.create_weapons(self.size, self.configuration)
        
    @staticmethod
    def create_weapons(size: float, config: RobotBuilder):
        return {
            w.id: Weapon(
                w.id, 
                w.normalized_x() * size, 
                w.normalized_y() * size, 
                w.angle * (math.pi / 180),
                w.type,
                get_weapon_stats(w.type)
            )
            for w in config.weapons
        }
        
    @staticmethod
    def create(configuration: RobotInterface, start_x: float, start_y: float, start_angle: float):
        stats = RobotStats()
        configuration.apply_stats(stats)    
        stats.make_allowable()
        stats.normalize()
        
        builder = RobotBuilder()
        configuration.build_robot(builder)
        
        return Robot(
            configuration,
            builder,
            stats,
            start_x, 
            start_y,
            start_angle, 
            configuration.do_ability
        )
            