import math
import pygame

from common.constants import MAX_HP, ROBOT_RADIUS
from common.game_state import GameState, PlayerColors


class GameRenderer:
    
    def __init__(self):
        self.state: GameState = None
        self.color_map: PlayerColors = None
        
    def render(self, screen: pygame.Surface):
        self._draw_players(screen)
        self._draw_projectiles(screen)
        self._draw_player_healthbars(screen)
        
    def _draw_players(self, screen: pygame.Surface):
        for player in self.state.players:
            pygame.draw.circle(screen, self.color_map.colors[player.idx], (player.x, player.y), ROBOT_RADIUS, 2)
            pygame.draw.line(screen, self.color_map.colors[player.idx], (player.x, player.y), (
                player.x + ROBOT_RADIUS * math.cos(player.angle),
                player.y + ROBOT_RADIUS * math.sin(player.angle)
            ))
            
    def _draw_projectiles(self, screen: pygame.Surface):
        for projectile in self.state.projectiles:
            pygame.draw.circle(screen, (253, 216, 53), (projectile.x, projectile.y), projectile.size)
            
    def _draw_player_healthbars(self, screen: pygame.Surface):
        for player in self.state.players:
            healthbar_width = ROBOT_RADIUS * 2
            healthbar_height = 5
            healthbar_offset = ROBOT_RADIUS + 10 + healthbar_height
            
            pygame.draw.rect(screen, (183, 28, 28), (
                player.x - healthbar_width / 2,
                player.y - healthbar_offset,
                healthbar_width, healthbar_height
            ))
            pygame.draw.rect(screen, (51, 105, 30), (
                player.x - healthbar_width / 2,
                player.y - healthbar_offset,
                healthbar_width * (player.hp / MAX_HP), healthbar_height
            ))