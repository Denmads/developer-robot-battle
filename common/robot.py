from dataclasses import dataclass, field
from typing import Callable

from common.robot_hull import RobotHullType, get_hull_instance
from common.robot_stats import RobotStats

@dataclass
class RobotBuilder:
    hull: RobotHullType = field(default=RobotHullType.STANDARD)


class RobotInterface:
    
    def build_robot(self, builder: RobotBuilder) -> None:
        pass
    
    def apply_stats(self, stats: RobotStats) -> None:
        pass

    def do_ability(self, index: int) -> None:
        pass
    



class Robot:
    
    def __init__(self, configuration: RobotBuilder, stats: RobotStats, x: int, y: int, angle: float, ability_func: Callable[[int], None]):
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
        self.energy_regen = self.hull.energy_regen + self.stats.energy_regen * 0.01