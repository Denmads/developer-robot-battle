import colorsys
from dataclasses import dataclass, field
import math
import random
from time import sleep
from typing import Callable

import pygame
from common.udp_message import GameStateMessage, PlayerStaticInfo, PlayerStaticInfoMessage, PlayerState, ProjectileState
from common.projectile import Projectile
from common.robot import Robot, RobotBuilder, RobotStats
from common.constants import ARENA_HEIGHT, ARENA_WIDTH
from server.player import Player


@dataclass
class PlayerKeyState:
    up: bool = field(init=False, default=False)
    down: bool = field(init=False, default=False)
    left: bool = field(init=False, default=False)
    right: bool = field(init=False, default=False)
    
    q: bool = field(init=False, default=False)
    w: bool = field(init=False, default=False)
    e: bool = field(init=False, default=False)
    a: bool = field(init=False, default=False)
    s: bool = field(init=False, default=False)
    d: bool = field(init=False, default=False)
    
    def clone(self) -> "PlayerKeyState":
        state = PlayerKeyState()
        
        state.up = self.up
        state.down = self.down
        state.left = self.left
        state.right = self.right
        
        state.q = self.q
        state.w = self.w
        state.e = self.e
        state.a = self.a
        state.s = self.s
        state.d = self.d
        
        return state

@dataclass
class PlayerInstance:
    idx: int
    robot: Robot
    dead: bool = field(default=False, init=False)
    
    # keys
    old_keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)
    keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)

class Game:
    
    def __init__(self, players: list[Player], send_udp: Callable[[object], None], game_ended: Callable[[], None], is_test: bool = False):
        self.send_udp = send_udp
        self.game_ended_callback = game_ended
        self.is_test = is_test
        
        self._initialize_players(players)
        
        self.projectiles: list[Projectile] = []
        
        self.running = False
        
    def _initialize_players(self, players: list[Player]):
        angle_step = math.pi * 2 / len(players)
        starting_dist_from_middle = 200
        middle_x = ARENA_WIDTH / 2
        middle_y = ARENA_HEIGHT / 2
        
        self.players: dict[str, PlayerInstance] = {}
        
        player_info: list[PlayerStaticInfo] = []
        for i, player in enumerate(players):
            stats = RobotStats()
            player.robot_configuration.apply_stats(stats)    
            stats.normalize()
            
            builder = RobotBuilder()
            player.robot_configuration.build_robot(builder)
            
            self.players[player.id] = PlayerInstance(
                i,
                Robot(
                    builder,
                    stats,
                    middle_x + starting_dist_from_middle * math.cos(angle_step * i), 
                    middle_y + starting_dist_from_middle * math.sin(angle_step * i),
                    angle_step * i + math.pi, 
                    player.robot_configuration.do_ability
                )
            )
            
            player_info.append(PlayerStaticInfo(
                i,
                self._get_random_player_color(),
                builder.hull,
                self.players[player.id].robot.size,
                self.players[player.id].robot.max_hp,
                self.players[player.id].robot.max_energy
            ))
            
        message = PlayerStaticInfoMessage()
        message.player_info = player_info
        self.send_udp(message)
        
    def _get_random_player_color(self) -> tuple[int, int, int]:
        h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
        return [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]
        
    def _alive_players(self) -> list[PlayerInstance]:
        return list(filter(lambda p: not p.dead, self.players.values()))
        
    def remove_disconnected_player(self, player: Player):
        del self.players[player.id]
        
    def run(self):
        self.running = True
        while self.running:
            for player in self._alive_players():
                
                self._update_from_input(player)
                player.old_keys = player.keys.clone()
                self._update_player(player)
                
            for projectile in self.projectiles:
                self._update_projectile(projectile)
                
            for p in list(filter(self._is_outside_screen, self.projectiles)):
                p.destroy = True
            self._check_collisions()
            
            self.projectiles = list(filter(lambda p: not p.destroy, self.projectiles))
                
            if not self.is_test and len(self._alive_players()) <= 1:
                self.running = False
                continue
                
            self.send_udp(self.get_state())
            sleep(1 / 20) # 20 updates per second
        
        self.game_ended_callback()
        
    def _update_from_input(self, player: PlayerInstance):
        robot_move_speed = player.robot.hull.speed + player.robot.stats.speed * 0.5
        robot_turn_speed = player.robot.hull.turn_speed + player.robot.stats.turn_speed * 0.02
        
        if player.keys.left:
            player.robot.angle -= robot_turn_speed
        if player.keys.right:
            player.robot.angle += robot_turn_speed
        
        dx = robot_move_speed * math.cos(player.robot.angle)
        dy = robot_move_speed * math.sin(player.robot.angle)
        
        new_pos_x = player.robot.x
        new_pos_y = player.robot.y
        
        if player.keys.up:
            new_pos_x = player.robot.x + dx
            new_pos_y = player.robot.y + dy
        if player.keys.down:
            new_pos_x = player.robot.x - dx
            new_pos_y = player.robot.y - dy
                
        if new_pos_x < player.robot.size:
            new_pos_x = player.robot.x + (player.robot.x - player.robot.size) * math.cos(player.robot.angle)
        elif new_pos_x > ARENA_WIDTH - player.robot.size:
            new_pos_x = player.robot.x + ((ARENA_WIDTH - player.robot.size) - player.robot.x) * math.cos(player.robot.angle)

        if new_pos_y < player.robot.size:
            new_pos_y = player.robot.y + (player.robot.y - player.robot.size) * math.sin(player.robot.angle)
        elif new_pos_y > ARENA_HEIGHT - player.robot.size:
            new_pos_y = player.robot.y + ((ARENA_HEIGHT - player.robot.size) - player.robot.y) * math.sin(player.robot.angle)

        player.robot.x = new_pos_x
        player.robot.y = new_pos_y
            
        if player.keys.q and not player.old_keys.q:
            player.robot.ability_func(1)
            
            if player.robot.energy >= 10:
                sx = player.robot.x + robot_move_speed * math.cos(player.robot.angle)
                sy = player.robot.y + robot_move_speed * math.sin(player.robot.angle)
                self.projectiles.append(Projectile(player.idx, sx, sy, player.robot.angle, 3, 10, 5))
                player.robot.energy -= 10
        elif player.keys.w and not player.old_keys.w:
            player.robot.ability_func(2)
        elif player.keys.e and not player.old_keys.e:
            player.robot.ability_func(3)
        elif player.keys.a and not player.old_keys.a:
            player.robot.ability_func(4)
        elif player.keys.s and not player.old_keys.s:
            player.robot.ability_func(5)
        elif player.keys.d and not player.old_keys.d:
            player.robot.ability_func(6)
            
    def _update_player(self, player: PlayerInstance):
        player.robot.energy = math.ceil(min(player.robot.max_energy, player.robot.energy + player.robot.energy_regen))
            
    def _update_projectile(self, projectile: Projectile):
        projectile.x += projectile.speed * math.cos(projectile.angle)
        projectile.y += projectile.speed * math.sin(projectile.angle)
            
    def _is_outside_screen(self, projectile: Projectile):
        return projectile.x < -projectile.size or projectile.x > ARENA_WIDTH + projectile.size or projectile.y < -projectile.size or projectile.y > ARENA_HEIGHT + projectile.size
            
    def _check_collisions(self):
        for projectile in self.projectiles:
            if projectile.destroy:
                continue
            
            for player in self._alive_players():
                if player.idx == projectile.owner_idx:
                    continue
                
                robot_radius_2 = player.robot.size * player.robot.size
                euclidean_dist = abs(player.robot.x - projectile.x) + abs(player.robot.y - projectile.y)
                
                if euclidean_dist < player.robot.size * 2:
                    dist = math.pow(player.robot.x - projectile.x, 2) + math.pow(player.robot.y - projectile.y, 2)
                    if dist < robot_radius_2:
                        projectile.destroy = True
                        player.robot.hp -= projectile.damage
                        
                        if player.robot.hp <= 0:
                            player.dead = True
            
    def get_state(self) -> GameStateMessage:
        state = GameStateMessage()
        
        state.players = [
            PlayerState(
                player.idx,
                round(player.robot.x),
                round(player.robot.y),
                player.robot.angle,
                round(player.robot.hp),
                round(player.robot.energy),
            ) 
            for player in self._alive_players()
        ]
        
        state.projectiles = [
            ProjectileState(
                round(projectile.x),
                round(projectile.y),
                projectile.angle,
                projectile.size
            )
            for projectile in self.projectiles
        ]
        
        return state
        
    def update_key(self, player_id: str, key: int, state: int):
            is_down = state == 1
            player = self.players[player_id]
        
            if key == pygame.K_UP:
                player.keys.up = is_down
            elif key == pygame.K_DOWN:
                player.keys.down = is_down
            elif key == pygame.K_LEFT:
                player.keys.left = is_down
            elif key == pygame.K_RIGHT:
                player.keys.right = is_down
                
            elif key == pygame.K_q:
                player.keys.q = is_down
            elif key == pygame.K_w:
                player.keys.w = is_down
            elif key == pygame.K_e:
                player.keys.e = is_down
            elif key == pygame.K_a:
                player.keys.a = is_down
            elif key == pygame.K_s:
                player.keys.s = is_down
            elif key == pygame.K_d:
                player.keys.d = is_down
        
    def stop(self):
        self.running = False
        