from datetime import timedelta

import pygame
from common.projectile import ProjectileModifier
from common.robot import RobotBuilder, RobotInfo, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import WeaponConfig, WeaponType
from common.weapon_command import WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.TOUGH
        
        builder.weapons.append(WeaponConfig("forward", 1, 0, 0, WeaponType.CANNON))
        builder.weapons.append(WeaponConfig("forwardRight", 1, 0.4, 20, WeaponType.CANNON))
        builder.weapons.append(WeaponConfig("forwardLeft", 1, -0.4, -20, WeaponType.CANNON))
        builder.weapons.append(WeaponConfig("mines", -0.9, 0, 180, WeaponType.MINE_DEPLOYER))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 2
        stats.turn_speed = 2
        stats.energy_regen = 1
        stats.max_energy = 2
        stats.max_health = 2
        stats.size = 1

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            command_list.append(WeaponCommand("forwardLeft", modifiers=[ProjectileModifier.EXPLOSIVE]))
        elif index == 2:
            command_list.append(WeaponCommand("forward", modifiers=[ProjectileModifier.EXPLOSIVE]))
        elif index == 3:
            command_list.append(WeaponCommand("forwardRight", modifiers=[ProjectileModifier.EXPLOSIVE]))
        elif index == 4:
            command_list.append(WeaponCommand("forward"))
            command_list.append(WeaponCommand("forwardLeft"))
        elif index == 5:
            command_list.append(WeaponCommand("mines", modifiers=[ProjectileModifier.EXPLOSIVE]))
        elif index == 6:
            command_list.append(WeaponCommand("forward"))
            command_list.append(WeaponCommand("forwardRight"))
            
    def get_state(self, info: RobotInfo) -> dict:
        pass
    
    def draw_gui(self, screen: pygame.Surface, arena_size: tuple[int, int], state: dict) -> None:
        pass