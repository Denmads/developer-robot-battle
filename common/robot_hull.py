from enum import IntEnum

from common.robot_stats import RobotStats


class RobotHullType(IntEnum):
    STANDARD = 1
    TOUGH = 2
    SPEEDY = 3
    

# Hulls
StandardHull = RobotStats(
    max_health=100,
    max_energy=100,
    energy_regen=0.06,
    move_speed=3.33,
    turn_speed=0.1,
    size=25
)

ToughHull = RobotStats(
    max_health=160,
    max_energy=80,
    energy_regen=0.06,
    move_speed=2,
    turn_speed=0.1,
    size=30
)

SpeedyHull = RobotStats(
    max_health=75,
    max_energy=80,
    energy_regen=0.06,
    move_speed=4.66,
    turn_speed=0.15,
    size=20
)

def get_hull_instance(type: RobotHullType) -> RobotStats:
    if type == RobotHullType.STANDARD:
        return StandardHull
    elif type == RobotHullType.TOUGH:
        return ToughHull
    elif type == RobotHullType.SPEEDY:
        return SpeedyHull