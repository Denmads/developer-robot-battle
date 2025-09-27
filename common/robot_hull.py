from enum import Enum

from common.robot_stats import RobotStats


class RobotHullType(Enum):
    STANDARD = 1
    TOUGH = 2
    SPEEDY = 3
    

# Hulls
StandardHull = RobotStats(
    max_health=100,
    max_energy=100,
    energy_regen=0.1,
    speed=5,
    turn_speed=0.1
)

ToughHull = RobotStats(
    max_health=160,
    max_energy=80,
    energy_regen=0.1,
    speed=3,
    turn_speed=0.1
)

SpeedyHull = RobotStats(
    max_health=75,
    max_energy=80,
    energy_regen=0.1,
    speed=7,
    turn_speed=0.15
)

def get_hull_instance(type: RobotHullType) -> RobotStats:
    if type == RobotHullType.STANDARD:
        return StandardHull
    elif type == RobotHullType.TOUGH:
        return ToughHull
    elif type == RobotHullType.SPEEDY:
        return SpeedyHull