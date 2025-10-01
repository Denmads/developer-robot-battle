from datetime import datetime
import math
import pygame

from common.calculations import calculate_weapon_point_offset
from common.constants import ARENA_HEIGHT, ARENA_WIDTH
from common.udp_message import GameStateMessage, PlayerState, PlayerStaticInfo, WeaponStaticInfo


class GameRenderer:
    
    def __init__(self):
        self.state: GameStateMessage = None
        self.static_player_info: dict[int, PlayerStaticInfo] = None
        self.round_start_time: datetime = None
        self.round_winner: str = None

        self.weapon_shape_points = [(-2.5, -2.5), (7.55, -2.5), (7.5, 2.5), (-2.5, 2.5)]

        pygame.font.init()
        self.announcement_font = pygame.font.SysFont("Arial", 72)
        self.announcement_secondary_font = pygame.font.SysFont("Arial", 56)
        
    def render(self, screen: pygame.Surface):
        if self.state is None:
            return
        
        self._draw_players(screen)
        self._draw_projectiles(screen)
        self._draw_player_health_and_energy_bars(screen)

        self._render_countdown_timer(screen)
        self._render_winner(screen)
        
    def _draw_players(self, screen: pygame.Surface):
        for player in self.state.players:
            player_info = self.static_player_info[player.idx]
            
            # DRAW PLAYER AND DIRECTION MARKER
            pygame.draw.circle(screen, player_info.color, (player.x, player.y), player_info.size, 2)
            pygame.draw.aaline(screen, player_info.color, 
                (
                    player.x + player_info.size * math.cos(player.angle) * 0.5,
                    player.y + player_info.size * math.sin(player.angle) * 0.5
                ), 
                (
                    player.x + player_info.size * math.cos(player.angle),
                    player.y + player_info.size * math.sin(player.angle)
                ))
            
            # DRAW HULL TYPE SYMBOL
            hull_type = player_info.hull
            num_points = hull_type + 2
            angle_step = math.pi * 2 / num_points
            
            points = [(
                player.x + player_info.size * 0.5 * math.cos(player.angle + angle_step * i),
                player.y + player_info.size * 0.5 * math.sin(player.angle + angle_step * i)
                ) for i in range(num_points)]
            
            pygame.draw.aalines(screen, (100, 100, 100), True, points)
            
            # DRAW WEAPONS
            for weapon in player_info.weapons:
                transformed_points = [
                    calculate_weapon_point_offset((player.x, player.y), player.angle, (weapon.x_offset, weapon.y_offset), weapon.angle, point)
                    for point in self.weapon_shape_points
                ]
                pygame.draw.polygon(screen, (150, 150, 150), transformed_points)
                
            
    def _draw_projectiles(self, screen: pygame.Surface):
        for projectile in self.state.projectiles:
            pygame.draw.circle(screen, (253, 216, 53), (projectile.x, projectile.y), projectile.size)
            
    def _draw_player_health_and_energy_bars(self, screen: pygame.Surface):
        for player in self.state.players:
            player_info = self.static_player_info[player.idx]
            bar_width = 30
            bar_height = 5
            bar_offset = player_info.size + 10 + bar_height
            
            # Health
            pygame.draw.rect(screen, (183, 28, 28), (
                player.x - bar_width / 2,
                player.y - (bar_offset + 2 * bar_height),
                bar_width, bar_height
            ))
            pygame.draw.rect(screen, (51, 105, 30), (
                player.x - bar_width / 2,
                player.y - (bar_offset + 2 * bar_height),
                bar_width * (player.hp / player_info.max_hp), bar_height
            ))
            
            # Energy
            pygame.draw.rect(screen, (2, 119, 189), (
                player.x - bar_width / 2,
                player.y - bar_offset,
                bar_width * (player.energy / player_info.max_energy), bar_height
            ))

    def _render_countdown_timer(self, screen: pygame.Surface):
        if self.round_start_time is not None and self.round_start_time > datetime.now():
            seconds_to_start = math.ceil((self.round_start_time - datetime.now()).total_seconds())
            countdown_surface = self.announcement_font.render(str(seconds_to_start), True, (255, 255, 255))
            screen.blit(countdown_surface, (ARENA_WIDTH / 2 - countdown_surface.get_width() / 2, ARENA_HEIGHT / 2 - countdown_surface.get_height() / 2 ))
            
    def _render_winner(self, screen: pygame.Surface):
        if self.round_winner:
            winner_surface = self.announcement_secondary_font.render(f"{self.round_winner} won", True, (255, 255, 255))
            screen.blit(winner_surface, (ARENA_WIDTH / 2 - winner_surface.get_width() / 2, ARENA_HEIGHT / 2 - winner_surface.get_height() / 2 ))