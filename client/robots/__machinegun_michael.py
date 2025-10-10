from datetime import timedelta

import pygame
from common.calculations import calculate_ability_energy_cost
from common.projectile import ProjectileModifier
from common.robot import Robot, RobotBuilder, RobotInfo, RobotInterface, RobotStats
from common.robot_hull import RobotHullType
from common.weapon import Weapon, WeaponConfig, WeaponType
from common.weapon_command import WeaponCommand


class MyRobot(RobotInterface):


    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 18)
        self.weapons: dict[str, Weapon] = {}

    def build_robot(self, builder: RobotBuilder) -> None:
        builder.hull = RobotHullType.STANDARD
        
        builder.weapons.append(WeaponConfig("forward", 1, 0, 0))
        builder.weapons.append(WeaponConfig("forwardRight", 1, 0.4, 20))
        builder.weapons.append(WeaponConfig("forwardLeft", 1, -0.4, -20))

        self.weapons = Robot.create_weapons(20, builder)
    
    def apply_stats(self, stats: RobotStats) -> None:
        stats.move_speed = 0
        stats.turn_speed = 0
        stats.energy_regen = 5
        stats.max_energy = 5
        stats.max_health = 0
        stats.size = 0

    def do_ability(self, index: int, command_list: list[WeaponCommand], info: RobotInfo) -> None:
        if index == 1:
            command_list += self._fire_projectiles("forwardLeft", 5, timedelta(milliseconds=200))
        elif index == 2:
            command_list += self._fire_projectiles("forward", 5, timedelta(milliseconds=200))
        elif index == 3:
            command_list += self._fire_projectiles("forwardRight", 5, timedelta(milliseconds=200))
        elif index == 4:
            command_list += self._fire_projectiles("forwardLeft", 5, timedelta(milliseconds=400))
            command_list += self._fire_projectiles("forward", 10, timedelta(milliseconds=200), timedelta(milliseconds=100))
            command_list += self._fire_projectiles("forwardRight", 5, timedelta(milliseconds=400), timedelta(milliseconds=200))
        elif index == 5:
            command_list += self._fire_as_many_as_possible("forward", timedelta(milliseconds=100), info)

    def _fire_projectiles(self, id: str, num_bullets: int, delay: timedelta, offset: timedelta = timedelta(milliseconds=0)) -> list[WeaponCommand]:
        commands = []
        for i in range(num_bullets):
            commands.append(WeaponCommand(id, offset + (delay * i)))
        return commands

    def _fire_as_many_as_possible(self, id: str, delay: timedelta, info: RobotInfo) -> list[WeaponCommand]:
        commands = []
        commands_next = [WeaponCommand(id, delay)]

        while calculate_ability_energy_cost(self.weapons, commands_next) < info.energy:
            commands = commands_next
            commands_next = commands_next.copy()
            commands_next.append(WeaponCommand(id, delay * len(commands)))

        return commands
            

    def get_state(self, info: RobotInfo) -> dict:
        num_fire_s_ability = len(self._fire_as_many_as_possible("forward", timedelta(milliseconds=100), info))

        return {
            "num_fire": num_fire_s_ability
        }
    
    def draw_gui(self, screen: pygame.Surface, arena_size: tuple[int, int], state: dict) -> None:
        text_surf = self.font.render(str(state["num_fire"]), True, (255, 255, 255))
        screen.blit(text_surf, (
            arena_size[0] - text_surf.get_width() - 20,
            arena_size[1] - text_surf.get_height() - 20
        ))