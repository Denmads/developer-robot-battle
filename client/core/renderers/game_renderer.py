from dataclasses import dataclass
from datetime import timedelta, datetime
import logging
import math
import pygame

from client.core.state_renderer import ClientState, SharedState, StateRenderer
from common.calculations import calculate_weapon_point_offset
from common.constants import MIN_AXIS_VALUE
from common.projectile import ProjectileModifier
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
        
        self.controller_left_active: bool = False
        self.controller_left_active_prev: bool = False
        self.controller_right_active: bool = False
        self.controller_right_active_prev: bool = False
        self.controller_up_active: bool = False
        self.controller_up_active_prev: bool = False
        self.controller_down_active: bool = False
        self.controller_down_active_prev: bool = False
        self.controller_rtrig_active: bool = False
        self.controller_rtrig_active_prev: bool = False
        self.controller_ltrig_active: bool = False
        self.controller_ltrig_active_prev: bool = False
        
        self.states: list[RenderState] = []
        self.total_state_time: timedelta = timedelta()
        self.time_in_state: timedelta = timedelta()
        
        self.robot_state: dict = None
        
        self.explosion_life_time: timedelta = timedelta(seconds=1)
        self.active_explosions: list[list[tuple[int, int, int], timedelta]] = []

        self.static_player_info: dict[int, PlayerStaticInfo] = None
        self.arena_size: tuple[int, int] = None
        self.round_start_time: datetime = None
        self.round_winner: str = None
        
        self.announcement_font = pygame.font.SysFont("Arial", 72)
        self.announcement_secondary_font = pygame.font.SysFont("Arial", 56)
    
    def add_new_state(self, state: GameStateMessage):
        self.states.append(RenderState(datetime.now(), state))
        self.time_in_state = timedelta()
        
        for expl in state.explosions:
            self.active_explosions.append([expl, timedelta(seconds=self.explosion_life_time.total_seconds())])

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
        elif self.state.client_state == ClientState.IN_TEST and ((event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE) or (event.type == pygame.JOYBUTTONDOWN and event.button == 4)): # button 4 == L Bumper
            self.state.tcp.send(ExitTestMessage())
        
        # Controller
        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 0: # X L-stick
                self.controller_left_active = event.value < -1 * MIN_AXIS_VALUE * 6
                self.controller_right_active = event.value > MIN_AXIS_VALUE * 6
                
                if self.controller_left_active and not self.controller_left_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_LEFT, 1))
                elif not self.controller_left_active and self.controller_left_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_LEFT, 2))
                    
                if self.controller_right_active and not self.controller_right_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_RIGHT, 1))
                elif not self.controller_right_active and self.controller_right_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_RIGHT, 2))
            elif event.axis == 1: # Y L-stick
                self.controller_up_active = event.value < -1 * MIN_AXIS_VALUE * 6
                self.controller_down_active = event.value > MIN_AXIS_VALUE * 6
                
                if self.controller_up_active and not self.controller_up_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_UP, 1))
                elif not self.controller_up_active and self.controller_up_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_UP, 2))
                    
                if self.controller_down_active and not self.controller_down_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_DOWN, 1))
                elif not self.controller_down_active and self.controller_down_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_DOWN, 2))
            elif event.axis == 4: # L Trig
                self.controller_ltrig_active = event.value < -1 + MIN_AXIS_VALUE * 6
                
                if self.controller_ltrig_active and not self.controller_ltrig_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_q, 1))
                elif not self.controller_ltrig_active and self.controller_ltrig_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_q, 2))
            elif event.axis == 5: # R Trig
                self.controller_rtrig_active = event.value < -1 + MIN_AXIS_VALUE * 6
                
                if self.controller_rtrig_active and not self.controller_rtrig_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_e, 1))
                elif not self.controller_rtrig_active and self.controller_rtrig_active_prev:
                    self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_e, 2))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: # A
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_s, 1))
            elif event.button == 1: # B
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_d, 1))
            elif event.button == 2: # X
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_a, 1))
            elif event.button == 3: # Y
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_w, 1))
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == 0: # A
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_s, 2))
            elif event.button == 1: # B
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_d, 2))
            elif event.button == 2: # X
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_a, 2))
            elif event.button == 3: # Y
                self.state.tcp.send(InputMessage(self.state.player_id, pygame.K_w, 2))
                
                
        self.controller_left_active_prev = self.controller_left_active
        self.controller_right_active_prev = self.controller_right_active
        self.controller_up_active_prev = self.controller_up_active
        self.controller_down_active_prev = self.controller_down_active
        self.controller_rtrig_active_prev = self.controller_rtrig_active
        self.controller_ltrig_active_prev = self.controller_ltrig_active
    
    def render(self, screen: pygame.Surface, delta: timedelta):
        self.time_in_state += delta
        
        if len(self.states) < 2:
            return
        
        for ex in self.active_explosions:
            ex[1] -= delta
        
        alpha = self.time_in_state / self.total_state_time if self.total_state_time.total_seconds() != 0 else 0
        try:

            self._draw_players(screen, alpha)
            self._draw_projectiles(screen, alpha)
            self._draw_explosions(screen, delta)
            self._draw_player_health_and_energy_bars(screen, alpha)
            
            self.state.robot.interface.draw_gui(screen, self.arena_size, self.robot_state)

            self._render_countdown_timer(screen)
            self._render_winner(screen)
            
        except Exception as ex:
            logging.getLogger().exception(ex)
            
        self.active_explosions = list(filter(lambda ex: ex[1].total_seconds() > 0, self.active_explosions))
        
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
            
            dx = p_x - proj_s0.x
            dy = p_y - proj_s0.y
            dist = dx * dx + dy * dy
            
            dx_n = dx / dist if dist != 0 else 0
            dy_n = dy / dist if dist != 0 else 0
            
            if proj_s1.modifiers & ProjectileModifier.BOUNCING > 0:
                pygame.draw.circle(screen, (124, 179, 66), (p_x, p_y), proj_s1.size + 2, 2)
                
            if proj_s1.modifiers & ProjectileModifier.HOMING > 0:
                pygame.draw.circle(screen, (171, 71, 188, 205), (p_x - (proj_s1.size + 10) * dx_n, p_y - (proj_s1.size + 10) * dy_n), proj_s1.size * 0.8)
                pygame.draw.circle(screen, (171, 71, 188, 135), (p_x - (proj_s1.size + 20) * dx_n, p_y - (proj_s1.size + 20) * dy_n), proj_s1.size * 0.5)
                pygame.draw.circle(screen, (171, 71, 188, 25), (p_x - (proj_s1.size + 30) * dx_n, p_y - (proj_s1.size + 30) * dy_n), proj_s1.size * 0.2)
                    
            if proj_s1.modifiers & ProjectileModifier.PIERCING > 0:
                pygame.draw.circle(screen, (84, 110, 122, 205), (p_x + (proj_s1.size * 4) * dx_n, p_y + (proj_s1.size * 4) * dy_n), proj_s1.size * 0.8)
            
            color = (211, 47, 47) if proj_s1.modifiers & ProjectileModifier.EXPLOSIVE > 0 else (253, 216, 53)
            pygame.draw.circle(screen, color, (p_x, p_y), proj_s1.size)
            
    def _draw_explosions(self, screen: pygame.Surface, delta: timedelta):
        for explosion in self.active_explosions:
            expl_progress = explosion[1] / self.explosion_life_time
            size = self.lerp(1, explosion[0][2], expl_progress)
            
            circle_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (211, 47, 47, 55), (size, size), size)
            
            screen.blit(circle_surf, (explosion[0][0] - size, explosion[0][1] - size))
            
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
    