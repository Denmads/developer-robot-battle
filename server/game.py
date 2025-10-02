import colorsys
from dataclasses import dataclass, field
from datetime import datetime
import math
import random
from time import sleep
from typing import Callable

import pygame
from common.calculations import calculate_weapon_point_offset
from common.udp_message import GameStateMessage, PlayerStaticInfo, PlayerStaticInfoMessage, PlayerState, ProjectileState, WeaponStaticInfo
from common.projectile import Projectile
from common.robot import Robot, RobotBuilder, RobotStats
from common.constants import ARENA_HEIGHT, ARENA_WIDTH
from common.weapon import WeaponCommand
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
    
    def __init__(self, players: list[Player], send_udp: Callable[[object], None], game_ended: Callable[[int], None], start_time: datetime, is_test: bool = False):
        self.send_udp = send_udp
        self.game_ended_callback = game_ended
        self.is_test = is_test
        self.start_time = start_time
        
        self.player_commands: dict[int, list[WeaponCommand]] = {}
        
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
            self.player_commands[i] = []
            
            stats = RobotStats()
            player.robot_configuration.apply_stats(stats)    
            stats.make_allowable()
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
                player.color,
                builder.hull,
                self.players[player.id].robot.size,
                [
                    WeaponStaticInfo(w.x, w.y, w.angle) 
                    for w in self.players[player.id].robot.weapons.values()],
                self.players[player.id].robot.max_hp,
                self.players[player.id].robot.max_energy
            ))
            
        message = PlayerStaticInfoMessage()
        message.player_info = player_info
        self.send_udp(message)
        
        
    def _alive_players(self) -> list[PlayerInstance]:
        return list(filter(lambda p: not p.dead, self.players.values()))
        
    def remove_disconnected_player(self, player: Player):
        del self.players[player.id]
        
    def run(self):
        self.running = True
        while self.running:
            if datetime.now() > self.start_time:

                for projectile in self.projectiles:
                    self._update_projectile(projectile)

                for player in self._alive_players():
                    
                    self._update_from_input(player)
                    player.old_keys = player.keys.clone()
                    self._update_player(player)    
                    
                for p in list(filter(self._is_outside_screen, self.projectiles)):
                    p.destroy = True
                self._check_collisions()
                
                self.projectiles = list(filter(lambda p: not p.destroy, self.projectiles))
                    
                if not self.is_test and len(self._alive_players()) <= 1:
                    self.running = False
                    continue
                
            self.send_udp(self.get_state())
            sleep(1 / 30) # 30 updates per second
        
        winner = self._alive_players()[0].idx if len(self._alive_players()) > 0 else -1
        self.game_ended_callback(winner)
        
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
            new_pos_x = player.robot.x + (player.robot.x - player.robot.size) * math.cos(player.robot.angle) * (-1 if player.keys.down else 1)
        elif new_pos_x > ARENA_WIDTH - player.robot.size:
            new_pos_x = player.robot.x + ((ARENA_WIDTH - player.robot.size) - player.robot.x) * math.cos(player.robot.angle) * (-1 if player.keys.down else 1)

        if new_pos_y < player.robot.size:
            new_pos_y = player.robot.y + (player.robot.y - player.robot.size) * math.sin(player.robot.angle) * (-1 if player.keys.down else 1)
        elif new_pos_y > ARENA_HEIGHT - player.robot.size:
            new_pos_y = player.robot.y + ((ARENA_HEIGHT - player.robot.size) - player.robot.y) * math.sin(player.robot.angle) * (-1 if player.keys.down else 1)

        player.robot.x = new_pos_x
        player.robot.y = new_pos_y
            
        new_commands: list[WeaponCommand] = []
        if player.keys.q and not player.old_keys.q and player.robot.energy > 10:
            player.robot.ability_func(1, new_commands)
            player.robot.energy -= 10
        elif player.keys.w and not player.old_keys.w and player.robot.energy > 10:
            player.robot.ability_func(2, new_commands)
            player.robot.energy -= 10
        elif player.keys.e and not player.old_keys.e and player.robot.energy > 10:
            player.robot.ability_func(3, new_commands)
            player.robot.energy -= 10
        elif player.keys.a and not player.old_keys.a and player.robot.energy > 10:
            player.robot.ability_func(4, new_commands)
            player.robot.energy -= 10
        elif player.keys.s and not player.old_keys.s and player.robot.energy > 10:
            player.robot.ability_func(5, new_commands)
            player.robot.energy -= 10
        elif player.keys.d and not player.old_keys.d and player.robot.energy > 10:
            player.robot.ability_func(6, new_commands)
            player.robot.energy -= 10
            
        for command in new_commands:
            command.time = datetime.now()
            
        self.player_commands[player.idx] += new_commands
            
    def _update_player(self, player: PlayerInstance):
        player.robot.energy = math.ceil(min(player.robot.max_energy, player.robot.energy + player.robot.energy_regen))
        
        completed: list[WeaponCommand] = []
        for command in self.player_commands[player.idx]:
            if command.time + command.delay < datetime.now():
                completed.append(command)
                weapon = player.robot.weapons[command.id]
                sx, sy = calculate_weapon_point_offset((player.robot.x, player.robot.y), player.robot.angle, (weapon.x, weapon.y), weapon.angle, (7.5, 0))
                p_angle = player.robot.angle + weapon.angle
                self.projectiles.append(Projectile(player.idx, sx, sy, p_angle, 3, 10, 5))
                
        for completed_command in completed:
            self.player_commands[player.idx].remove(completed_command)
            
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
                player.robot.x,
                player.robot.y,
                player.robot.angle,
                round(player.robot.hp),
                round(player.robot.energy),
            ) 
            for player in self._alive_players()
        ]
        
        state.projectiles = [
            ProjectileState(
                projectile.x,
                projectile.y,
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
        