import math
import pygame

from common.constants import MAX_HP, ROBOT_RADIUS
from common.game_state import GameState, PlayerInfo
from common.robot_hull import RobotHullType


class GameRenderer:
    
    def __init__(self):
        self.state: GameState = None
        self.static_player_info: PlayerInfo = None
        
    def render(self, screen: pygame.Surface):
        if self.state is None:
            return
        
        self._draw_players(screen)
        self._draw_projectiles(screen)
        self._draw_player_health_and_energy_bars(screen)
        
    def _draw_players(self, screen: pygame.Surface):
        for player in self.state.players:
            pygame.draw.circle(screen, self.static_player_info.colors[player.idx], (player.x, player.y), ROBOT_RADIUS, 2)
            pygame.draw.aaline(screen, self.static_player_info.colors[player.idx], 
                (
                    player.x + ROBOT_RADIUS * math.cos(player.angle) * 0.5,
                    player.y + ROBOT_RADIUS * math.sin(player.angle) * 0.5
                ), 
                (
                    player.x + ROBOT_RADIUS * math.cos(player.angle),
                    player.y + ROBOT_RADIUS * math.sin(player.angle)
                ))
            
            hull_type = self.static_player_info.hulls[player.idx]
            num_points = hull_type.value + 2
            angle_step = math.pi * 2 / num_points
            
            points = [(
                player.x + ROBOT_RADIUS * 0.5 * math.cos(player.angle + angle_step * i),
                player.y + ROBOT_RADIUS * 0.5 * math.sin(player.angle + angle_step * i)
                ) for i in range(num_points)]
            
            pygame.draw.aalines(screen, (100, 100, 100), True, points)
            
    def _draw_projectiles(self, screen: pygame.Surface):
        for projectile in self.state.projectiles:
            pygame.draw.circle(screen, (253, 216, 53), (projectile.x, projectile.y), projectile.size)
            
    def _draw_player_health_and_energy_bars(self, screen: pygame.Surface):
        for player in self.state.players:
            bar_width = ROBOT_RADIUS * 2
            bar_height = 5
            bar_offset = ROBOT_RADIUS + 10 + bar_height
            
            # Health
            pygame.draw.rect(screen, (183, 28, 28), (
                player.x - bar_width / 2,
                player.y - (bar_offset + 2 * bar_height),
                bar_width, bar_height
            ))
            pygame.draw.rect(screen, (51, 105, 30), (
                player.x - bar_width / 2,
                player.y - (bar_offset + 2 * bar_height),
                bar_width * (player.hp / player.max_hp), bar_height
            ))
            
            # Energy
            pygame.draw.rect(screen, (2, 119, 189), (
                player.x - bar_width / 2,
                player.y - bar_offset,
                bar_width * (player.energy / player.max_energy), bar_height
            ))