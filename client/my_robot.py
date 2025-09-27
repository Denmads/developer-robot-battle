from common.robot import RobotBuilder, RobotInterface, RobotStats
from common.robot_hull import RobotHullType


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.SPEEDY
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 1
        stats.max_energy = 1
        stats.max_health = 1

    def do_ability(self, index: int) -> None:
        pass