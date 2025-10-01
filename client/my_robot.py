from common.robot import RobotBuilder, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import Weapon, WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.SPEEDY
        
        builder.weapons.append(Weapon("wf", 0.5, -0.5, 315))
        builder.weapons.append(Weapon("wr", -0.5, -0.5, 225))
        builder.weapons.append(Weapon("wb", -0.5, 0.5, 135))
        builder.weapons.append(Weapon("wl", 0.5, 0.5, 45))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 1
        stats.max_energy = 1
        stats.max_health = 1

    def do_ability(self, index: int, command_list: list[WeaponCommand]) -> None:
        if index == 1:
            command_list.append(WeaponCommand("wf"))
        elif index == 2:
            command_list.append(WeaponCommand("wr"))
        elif index == 3:
            command_list.append(WeaponCommand("wb"))
        elif index == 4:
            command_list.append(WeaponCommand("wl"))
        elif index == 5:
            command_list.append(WeaponCommand("wf"))
            command_list.append(WeaponCommand("wr"))
        elif index == 6:
            command_list.append(WeaponCommand("wb"))
            command_list.append(WeaponCommand("wl"))