from dataclasses import dataclass, field
import math

from common.constants import TOTAL_STAT_POINTS


@dataclass
class RobotStats:
    max_health: float = field(default=1)
    max_energy: float = field(default=1)
    energy_regen: float = field(default=1)
    move_speed: float = field(default=1)
    turn_speed: float = field(default=1)
    size: float = field(default=1)
    
    def make_allowable(self):
        if math.isinf(self.max_health) or math.isnan(self.max_health):
            self.max_health = 1 
        if math.isinf(self.max_energy) or math.isnan(self.max_energy):
            self.max_energy = 1
        if math.isinf(self.energy_regen) or math.isnan(self.energy_regen):
            self.energy_regen = 1
        if math.isinf(self.move_speed) or math.isnan(self.move_speed):
            self.move_speed = 1
        if math.isinf(self.turn_speed) or math.isnan(self.turn_speed):
            self.turn_speed = 1
        if math.isinf(self.size) or math.isnan(self.size):
            self.size = 1

        self.max_health = abs(self.max_health)
        self.max_energy = abs(self.max_energy)
        self.energy_regen = abs(self.energy_regen)
        self.move_speed = abs(self.move_speed)
        self.turn_speed = abs(self.turn_speed)
        self.size = abs(self.size)

    def normalize(self):
        

        total = self.max_health + self.max_energy + self.energy_regen + self.move_speed + self.turn_speed + self.size
        scale = TOTAL_STAT_POINTS / total
        
        self.max_health = self.max_health * scale
        self.max_energy = self.max_energy * scale
        self.energy_regen = self.energy_regen * scale
        self.move_speed = self.move_speed * scale
        self.turn_speed = self.turn_speed * scale
        self.size = self.size * scale