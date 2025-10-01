from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math


@dataclass
class Weapon:
    id: str
    x: float
    y: float
    angle: float
    
    def normalized_x(self) -> float:
        length = math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
        return self.x / length if length > 1 else self.x
    
    def normalized_y(self) -> float:
        length = math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
        return self.y / length if length > 1 else self.y
    
@dataclass
class WeaponCommand:
    id: str
    time: datetime = field(default_factory=datetime.now, init=False)
    delay: timedelta = field(default=timedelta(seconds=0), init=False)