import pygame
from common.projectile import ProjectileModifier
from common.robot import RobotBuilder, RobotInfo, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import WeaponConfig, WeaponType
from common.weapon_command import WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.STANDARD
        
        builder.weapons.append(WeaponConfig("sn", 1, 0, 0, WeaponType.SNIPER))
        builder.weapons.append(WeaponConfig("b", 1, 0, 0, WeaponType.STANDARD))
        builder.weapons.append(WeaponConfig("m", -1, 0, 180, WeaponType.MINE_DEPLOYER))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 1
        stats.max_energy = 1
        stats.max_health = 1
        stats.size = 1

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            command_list.append(WeaponCommand("sn", modifiers=[ProjectileModifier.BOUNCING]))
        if index == 2:
            command_list.append(WeaponCommand("m"))
        if index == 3:
            command_list.append(WeaponCommand("b", modifiers=[ProjectileModifier.BOUNCING]))
        if index == 4:
            command_list.append(WeaponCommand("b", modifiers=[ProjectileModifier.PIERCING]))
        if index == 5:
            command_list.append(WeaponCommand("b", modifiers=[ProjectileModifier.HOMING]))
        if index == 6:
            command_list.append(WeaponCommand("b", modifiers=[ProjectileModifier.EXPLOSIVE]))
            
    def get_state(self, info: RobotInfo) -> dict:
        return {}
    
    def draw_gui(self, screen: pygame.Surface, arena_size: tuple[int, int], state: dict) -> None:
        pass