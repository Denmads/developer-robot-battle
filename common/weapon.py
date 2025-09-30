from dataclasses import dataclass
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