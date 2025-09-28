from dataclasses import dataclass, field

from common.constants import TOTAL_STAT_POINTS


@dataclass
class RobotStats:
    max_health: float = field(default=1)
    max_energy: float = field(default=1)
    energy_regen: float = field(default=1)
    speed: float = field(default=1)
    turn_speed: float = field(default=1)
    size: float = field(default=1)
    
    def normalize(self):
        total = self.max_health + self.max_energy + self.energy_regen + self.speed + self.turn_speed + self.size
        scale = TOTAL_STAT_POINTS / total
        
        self.max_health = self.max_health * scale
        self.max_energy = self.max_energy * scale
        self.energy_regen = self.energy_regen * scale
        self.speed = self.speed * scale
        self.turn_speed = self.turn_speed * scale
        self.size = self.size * scale