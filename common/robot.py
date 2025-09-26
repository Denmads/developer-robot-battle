from typing import Callable

from common.constants import MAX_HP


class RobotInterface:
    
    def create_robot(self) -> None:
        pass

    def do_ability(self, index: int) -> None:
        pass
    

class Robot:
    
    def __init__(self, x: int, y: int, angle: float, ability_func: Callable[[int], None]):
        self.ability_func = ability_func
        self.x = x
        self.y = y
        self.angle = angle
        self.hp = MAX_HP