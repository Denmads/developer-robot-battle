from datetime import timedelta
import math

import pygame
from common.calculations import calculate_ability_energy_cost
from common.projectile import ProjectileModifier
from common.robot import Robot, RobotBuilder, RobotInfo, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import Weapon, WeaponConfig, WeaponType
from common.weapon_command import WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.TOUGH
        
        builder.weapons.append(WeaponConfig("sniper", 1, 0, 0, WeaponType.SNIPER))
        builder.weapons.append(WeaponConfig("mines", -1, 0, 180, WeaponType.MINE_DEPLOYER))
        builder.weapons.append(WeaponConfig("forwardRight", 1, 0.4, 20))
        builder.weapons.append(WeaponConfig("forwardLeft", 1, -0.4, -20))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 3
        stats.max_energy = 2
        stats.max_health = 1
        stats.size = 2

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            command_list += self._fire_projectiles("forwardLeft", 5, timedelta(milliseconds=100))
        elif index == 2:
            command_list.append(WeaponCommand("sniper", modifiers=[ProjectileModifier.PIERCING]))
            command_list.append(WeaponCommand("sniper", timedelta(milliseconds=100), modifiers=[ProjectileModifier.EXPLOSIVE]))
        elif index == 3:
            command_list += self._fire_projectiles("forwardRight", 5, timedelta(milliseconds=100))
        elif index == 4:
            command_list += self._fire_projectiles("forwardLeft", 3, timedelta(milliseconds=100), modifiers=[ProjectileModifier.BOUNCING])
        elif index == 5:
            command_list.append(WeaponCommand("forwardLeft", modifiers=[ProjectileModifier.HOMING]))
            command_list.append(WeaponCommand("forwardRight", modifiers=[ProjectileModifier.HOMING]))
            command_list.append(WeaponCommand("mines"))
        elif index == 6:
            command_list += self._fire_projectiles("forwardRight", 3, timedelta(milliseconds=100), modifiers=[ProjectileModifier.PIERCING])
    
    def _fire_projectiles(self, id: str, num_bullets: int, delay: timedelta, offset: timedelta = timedelta(milliseconds=0), modifiers: list[ProjectileModifier] = None) -> list[WeaponCommand]:
        
        if modifiers is None:
            modifiers = []
        
        commands = []
        for i in range(num_bullets):
            commands.append(WeaponCommand(id, offset + (delay * i), modifiers=modifiers))
        return commands

    def get_state(self, info: RobotInfo) -> dict:
        return {}
    
    def draw_gui(self, screen: pygame.Surface, arena_size: tuple[int, int], state: dict) -> None:
        pass