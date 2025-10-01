from common.robot import RobotBuilder, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import Weapon, WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.SPEEDY
        
        builder.weapons.append(Weapon("fl", 0.5, -0.5, 315))
        builder.weapons.append(Weapon("bl", -0.5, -0.5, 225))
        builder.weapons.append(Weapon("br", -0.5, 0.5, 135))
        builder.weapons.append(Weapon("fr", 0.5, 0.5, 45))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 1
        stats.max_energy = 1
        stats.max_health = 1
        stats.size = 1

    def do_ability(self, index: int, command_list: list[WeaponCommand]) -> None:
        if index == 1:
            command_list.append(WeaponCommand("fl"))
        elif index == 2:
            command_list.append(WeaponCommand("bl"))
        elif index == 3:
            command_list.append(WeaponCommand("br"))
        elif index == 4:
            command_list.append(WeaponCommand("fr"))
        elif index == 5:
            command_list.append(WeaponCommand("fl"))
            command_list.append(WeaponCommand("bl"))
        elif index == 6:
            command_list.append(WeaponCommand("br"))
            command_list.append(WeaponCommand("fr"))