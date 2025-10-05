from dataclasses import dataclass
from datetime import timedelta, datetime
import math
import pygame

from client.core.state_renderer import ClientState, SharedState, StateRenderer
from common.calculations import calculate_weapon_point_offset
from common.tcp_messages import ExitTestMessage, InputMessage, RoundStartedMessage
from common.udp_message import GameStateMessage, PlayerStaticInfo


@dataclass
class RenderState:
    time: datetime
    state: GameStateMessage
    
WEAPON_SHAPE_POINTS = [(-2.5, -2.5), (7.55, -2.5), (7.5, 2.5), (-2.5, 2.5)]

ALLOWED_KEYS = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a, pygame.K_s, pygame.K_d,
                pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]

class GameStateRenderer(StateRenderer):
    
    def __init__(self, state: SharedState):
        super().__init__(state)
        
        self.states: list[RenderState] = []
        self.total_state_time: timedelta = timedelta()
        self.time_in_state: timedelta = timedelta()
        
        self.robot_state: dict = None

        self.static_player_info: dict[int, PlayerStaticInfo] = None
        self.arena_size: tuple[int, int] = None
        self.round_start_time: datetime = None
        self.round_winner: str = None
        
        self.announcement_font = pygame.font.SysFont("Arial", 72)
        self.announcement_secondary_font = pygame.font.SysFont("Arial", 56)
    
    def add_new_state(self, state: GameStateMessage):
        self.states.append(RenderState(datetime.now(), state))
        self.time_in_state = timedelta()

        if len(self.states) > 2:
            self.states.pop(0)

        if len(self.states) == 2:
            self.total_state_time = self.states[1].time - self.states[0].time
            
    def start_round(self, message: RoundStartedMessage):
        self.round_start_time = datetime.fromisoformat(message.begin_time)
        self.arena_size = (message.arena_width, message.arena_height)
        
    def set_winner(self, winner_id: str):
        self.round_winner = winner_id

    def lerp(self, v1: float, v2: float, alpha: float) -> float:
        return v1 + (v2 - v1) * alpha
    
    def on_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key in ALLOWED_KEYS:
            self.state.tcp.send(InputMessage(self.state.player_id, event.key, 1))
        elif event.type == pygame.KEYUP and event.key in ALLOWED_KEYS:
            self.state.tcp.send(InputMessage(self.state.player_id, event.key, 2))
        elif self.state.client_state == ClientState.IN_TEST and event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.state.tcp.send(ExitTestMessage())
    
    def render(self, screen: pygame.Surface, delta: timedelta):
        self.time_in_state += delta
        
        if len(self.states) < 2:
            return

        alpha = self.time_in_state / self.total_state_time if self.total_state_time.total_seconds() != 0 else 0

        self._draw_players(screen, alpha)
        self._draw_projectiles(screen, alpha)
        self._draw_player_health_and_energy_bars(screen, alpha)
        
        self.state.robot.interface.draw_gui(screen, self.robot_state)

        self._render_countdown_timer(screen)
        self._render_winner(screen)
        
    def _draw_players(self, screen: pygame.Surface, alpha: float):
        for p_idx in range(len(self.states[1].state.players)):
            player_s0 = self.states[0].state.players[p_idx]
            player_s1 = self.states[1].state.players[p_idx]
            player_info = self.static_player_info[player_s1.idx]
            
            p_x = self.lerp(player_s0.x, player_s1.x, alpha)
            p_y = self.lerp(player_s0.y, player_s1.y, alpha)
            p_angle = self.lerp(player_s0.angle, player_s1.angle, alpha)

            # DRAW PLAYER AND DIRECTION MARKER
            pygame.draw.circle(screen, player_info.color, (
                p_x, 
                p_y), 
                player_info.size, 2)
            pygame.draw.aaline(screen, player_info.color, 
                (
                    p_x + player_info.size * math.cos(p_angle) * 0.5,
                    p_y + player_info.size * math.sin(p_angle) * 0.5
                ), 
                (
                    p_x + player_info.size * math.cos(p_angle),
                    p_y + player_info.size * math.sin(p_angle)
                ))
            
            # DRAW HULL TYPE SYMBOL
            hull_type = player_info.hull
            num_points = hull_type + 2
            angle_step = math.pi * 2 / num_points
            
            points = [(
                p_x + player_info.size * 0.5 * math.cos(p_angle + angle_step * i),
                p_y + player_info.size * 0.5 * math.sin(p_angle + angle_step * i)
                ) for i in range(num_points)]
            
            pygame.draw.aalines(screen, (100, 100, 100), True, points)
            
            # DRAW WEAPONS
            for weapon in player_info.weapons:
                transformed_points = [
                    calculate_weapon_point_offset((p_x, p_y), p_angle, (weapon.x_offset, weapon.y_offset), weapon.angle, point)
                    for point in WEAPON_SHAPE_POINTS
                ]
                pygame.draw.polygon(screen, (150, 150, 150), transformed_points)
                
            
    def _draw_projectiles(self, screen: pygame.Surface, alpha: float):
        for p_idx in range(len(self.states[1].state.projectiles)):
            proj_s1 = self.states[1].state.projectiles[p_idx]
            s0_lookup = list(filter(lambda p: p.id == proj_s1.id, self.states[0].state.projectiles))
            proj_s0 = s0_lookup[0] if len(s0_lookup) > 0 else None

            if proj_s0 is None:
                continue

            p_x = self.lerp(proj_s0.x, proj_s1.x, alpha)
            p_y = self.lerp(proj_s0.y, proj_s1.y, alpha)

            pygame.draw.circle(screen, (253, 216, 53), (p_x, p_y), proj_s1.size)
            
    def _draw_player_health_and_energy_bars(self, screen: pygame.Surface, alpha: float):
        for p_idx in range(len(self.states[1].state.players)):
            player_s0 = self.states[0].state.players[p_idx]
            player_s1 = self.states[1].state.players[p_idx]
            player_info = self.static_player_info[player_s1.idx]

            p_x = self.lerp(player_s0.x, player_s1.x, alpha)
            p_y = self.lerp(player_s0.y, player_s1.y, alpha)

            bar_width = 30
            bar_height = 5
            bar_offset = player_info.size + 10 + bar_height
            
            # Health
            pygame.draw.rect(screen, (183, 28, 28), (
                p_x - bar_width / 2,
                p_y - (bar_offset + 2 * bar_height),
                bar_width, bar_height
            ))
            pygame.draw.rect(screen, (51, 105, 30), (
                p_x - bar_width / 2,
                p_y - (bar_offset + 2 * bar_height),
                bar_width * (player_s1.hp / player_info.max_hp), bar_height
            ))
            
            # Energy
            pygame.draw.rect(screen, (2, 119, 189), (
                p_x - bar_width / 2,
                p_y - bar_offset,
                bar_width * (player_s1.energy / player_info.max_energy), bar_height
            ))

    def _render_countdown_timer(self, screen: pygame.Surface):
        if self.round_start_time is not None and self.round_start_time > datetime.now():
            seconds_to_start = math.ceil((self.round_start_time - datetime.now()).total_seconds())
            countdown_surface = self.announcement_font.render(str(seconds_to_start), True, (255, 255, 255))
            screen.blit(countdown_surface, (self.arena_size[0] / 2 - countdown_surface.get_width() / 2, self.arena_size[1] / 2 - countdown_surface.get_height() / 2 ))
            
    def _render_winner(self, screen: pygame.Surface):
        if self.round_winner:
            winner_surface = self.announcement_secondary_font.render(f"{self.round_winner} won", True, (255, 255, 255))
            screen.blit(winner_surface, (self.arena_size[0] / 2 - winner_surface.get_width() / 2, self.arena_size[1] / 2 - winner_surface.get_height() / 2 ))
    