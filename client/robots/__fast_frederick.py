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

    def __init__(self):
        self.num_weapons = 8


    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.STANDARD
        
        angle_spacing = math.pi * 2 / self.num_weapons
        for i in range(8):
            angle = angle_spacing * i
            builder.weapons.append(WeaponConfig(f"w{i}", math.cos(angle), math.sin(angle), angle * (180/math.pi), WeaponType.SNIPER))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 2
        stats.turn_speed = 2
        stats.energy_regen = 3
        stats.max_energy = 2
        stats.max_health = 1
        stats.size = 0

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            for i in range(0, self.num_weapons, 2):
                command_list.append(WeaponCommand(f"w{i}"))
        elif index == 2:
            for i in range(0, self.num_weapons):
                command_list.append(WeaponCommand(f"w{i}", timedelta(milliseconds=50) * i))
        elif index == 3:
            for i in range(1, self.num_weapons, 2):
                command_list.append(WeaponCommand(f"w{i}"))
        elif index == 4:
            for i in range(0, self.num_weapons, 2):
                command_list.append(WeaponCommand(f"w{i}", modifiers=[ProjectileModifier.BOUNCING]))
        elif index == 5:
            for i in range(0, self.num_weapons):
                command_list.append(WeaponCommand(f"w{i}", timedelta(milliseconds=50) * i, modifiers=[ProjectileModifier.BOUNCING]))
        elif index == 6:
            for i in range(1, self.num_weapons, 2):
                command_list.append(WeaponCommand(f"w{i}", modifiers=[ProjectileModifier.BOUNCING]))
            

    def get_state(self, info: RobotInfo) -> dict:
        return {}
    
    def draw_gui(self, screen: pygame.Surface, arena_size: tuple[int, int], state: dict) -> None:
        pass