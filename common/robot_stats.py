from dataclasses import dataclass, field
import math

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
        if math.isinf(self.max_health):
            self.max_health = 1000000
        if math.isinf(self.max_energy):
            self.max_energy = 1000000
        if math.isinf(self.energy_regen):
            self.energy_regen = 1000000
        if math.isinf(self.speed):
            self.speed = 1000000
        if math.isinf(self.turn_speed):
            self.turn_speed = 1000000
        if math.isinf(self.size):
            self.size = 1000000

        total = self.max_health + self.max_energy + self.energy_regen + self.speed + self.turn_speed + self.size
        scale = TOTAL_STAT_POINTS / total
        
        self.max_health = self.max_health * scale
        self.max_energy = self.max_energy * scale
        self.energy_regen = self.energy_regen * scale
        self.speed = self.speed * scale
        self.turn_speed = self.turn_speed * scale
        self.size = self.size * scale