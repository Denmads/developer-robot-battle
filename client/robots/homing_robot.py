import pygame
from common.projectile import ProjectileModifier
from common.robot import RobotBuilder, RobotInfo, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import WeaponConfig, WeaponCommand


class MyRobot(RobotInterface):

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.SPEEDY
        
        builder.weapons.append(WeaponConfig("w", 1, 0, 0))
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 1
        stats.turn_speed = 1
        stats.energy_regen = 1
        stats.max_energy = 1
        stats.max_health = 1
        stats.size = 1

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            command_list.append(WeaponCommand("w", modifiers=[ProjectileModifier.PIERCING, ProjectileModifier.BOUNCING]))
            
    def get_state(self) -> dict:
        return {}
    
    def draw_gui(self, screen: pygame.Surface, state: dict) -> None:
        pass