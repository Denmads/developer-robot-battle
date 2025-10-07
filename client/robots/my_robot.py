from datetime import timedelta

import pygame
from common.robot import RobotBuilder, RobotInfo, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import WeaponConfig
from common.weapon_command import WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.SPEEDY
        
        builder.weapons.append(WeaponConfig("fl", 0.5, -0.5, 315))
        builder.weapons.append(WeaponConfig("bl", -0.5, -0.5, 225))
        builder.weapons.append(WeaponConfig("br", -0.5, 0.5, 135))
        builder.weapons.append(WeaponConfig("fr", 0.5, 0.5, 45))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 1
        stats.max_energy = 1
        stats.max_health = 1
        stats.size = 1

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            command_list.append(WeaponCommand("fl"))
        elif index == 2:
            command_list.append(WeaponCommand("bl"))
            command_list.append(WeaponCommand("bl", delay=timedelta(milliseconds=100)))
            command_list.append(WeaponCommand("bl", delay=timedelta(milliseconds=200)))
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
            
    def get_state(self) -> dict:
        return {}
    
    def draw_gui(self, screen: pygame.Surface, state: dict) -> None:
        pygame.draw.rect(screen, (255, 0, 0), (0,0,100,100))