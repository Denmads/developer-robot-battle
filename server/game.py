import colorsys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
import random
from time import sleep
from typing import Callable

import pygame
from common.arena import Arena
from common.calculations import calculate_ability_energy_cost, calculate_weapon_point_offset
from common.udp_message import GameStateMessage, PlayerStaticInfo, PlayerStaticInfoMessage, PlayerState, ProjectileState, RobotStateMessage, WeaponStaticInfo
from common.projectile import Projectile
from common.robot import RobotInfo, Robot, RobotBuilder, RobotStats
from common.weapon import WeaponCommand, get_weapon_stats
from server.player import Player
from server.spatial_grid import SpatialGrid
from server.udp_socket import UDPSocket


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
    player: Player
    robot: Robot
    dead: bool = field(default=False, init=False)
    
    # keys
    old_keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)
    keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)

class Game:
    
    def __init__(self, players: list[Player], arena: Arena, udp: UDPSocket, game_ended: Callable[[int], None], start_time: datetime, is_test: bool = False):
        self.arena = arena
        self.udp = udp
        self.game_ended_callback = game_ended
        self.is_test = is_test
        self.start_time = start_time
        
        self.player_commands: dict[int, list[WeaponCommand]] = {}
        self.spatial_grid: SpatialGrid = SpatialGrid(100)
        
        self._initialize_players(players)
        
        self.projectiles: list[Projectile] = []
        self.projectile_id_counter: int = 0
        
        self.running = False
        
    def _initialize_players(self, players: list[Player]):
        angle_step = math.pi * 2 / len(players)
        starting_dist_from_middle = 200
        middle_x = self.arena.width / 2
        middle_y = self.arena.height / 2
        
        self.players: dict[str, PlayerInstance] = {}
        
        player_info: list[PlayerStaticInfo] = []
        for i, player in enumerate(players):
            self.player_commands[i] = []
            
            self.players[player.id] = PlayerInstance(
                i,
                player,
                Robot.create(
                    player.robot_configuration,
                    middle_x + starting_dist_from_middle * math.cos(angle_step * i), 
                    middle_y + starting_dist_from_middle * math.sin(angle_step * i),
                    angle_step * i + math.pi
                )
            )
            
            player_info.append(PlayerStaticInfo(
                i,
                player.color,
                self.players[player.id].robot.configuration.hull,
                self.players[player.id].robot.size,
                [
                    WeaponStaticInfo(w.x, w.y, w.angle, w.type) 
                    for w in self.players[player.id].robot.weapons.values()],
                self.players[player.id].robot.max_hp,
                self.players[player.id].robot.max_energy
            ))
            
        message = PlayerStaticInfoMessage()
        message.player_info = player_info
        self.udp.send_to_all(message)
        
        
    def _alive_players(self) -> list[PlayerInstance]:
        return list(filter(lambda p: not p.dead, self.players.values()))
        
    def remove_disconnected_player(self, player: Player):
        del self.players[player.id]
        
    def run(self):
        self.running = True
        last_update = datetime.now()
        while self.running:
            if datetime.now() > self.start_time:
                delta = datetime.now() - last_update
                self.spatial_grid.clear()
                for projectile in self.projectiles:
                    self._update_projectile(projectile)

                for player in self._alive_players():
                    
                    self._update_from_input(player)
                    player.old_keys = player.keys.clone()
                    self._update_player(player, delta)    
                    
                for p in list(filter(self._is_outside_screen, self.projectiles)):
                    p.destroy = True
                self._check_collisions()
                
                self.projectiles = list(filter(lambda p: not p.destroy, self.projectiles))
                    
                if not self.is_test and len(self._alive_players()) <= 1:
                    self.running = False
                    continue
                
            self.udp.send_to_all(self.get_state())
            for id, instance in self.players.items():
                robot_state = self.get_robot_state(id)
                message = RobotStateMessage()
                message.state = robot_state
                self.udp.send_to_player(instance.player, message)
            
            last_update = datetime.now()
            sleep(1 / 30) # 30 updates per second
        
        winner = self._alive_players()[0].idx if len(self._alive_players()) > 0 else -1
        self.game_ended_callback(winner)
        
    def _update_from_input(self, player: PlayerInstance):
        
        if player.keys.left:
            player.robot.angle -= player.robot.turn_speed
        if player.keys.right:
            player.robot.angle += player.robot.turn_speed
        
        dx = player.robot.move_speed * math.cos(player.robot.angle)
        dy = player.robot.move_speed * math.sin(player.robot.angle)
        
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
        elif new_pos_x > self.arena.width - player.robot.size:
            new_pos_x = player.robot.x + ((self.arena.width - player.robot.size) - player.robot.x) * math.cos(player.robot.angle) * (-1 if player.keys.down else 1)

        if new_pos_y < player.robot.size:
            new_pos_y = player.robot.y + (player.robot.y - player.robot.size) * math.sin(player.robot.angle) * (-1 if player.keys.down else 1)
        elif new_pos_y > self.arena.height - player.robot.size:
            new_pos_y = player.robot.y + ((self.arena.height - player.robot.size) - player.robot.y) * math.sin(player.robot.angle) * (-1 if player.keys.down else 1)

        player.robot.x = new_pos_x
        player.robot.y = new_pos_y
            
        new_commands: list[WeaponCommand] = []
        info = RobotInfo(
            player.robot.hp,
            player.robot.max_hp,
            player.robot.energy,
            player.robot.max_energy,
            {
                w.id: w.cooldown_time_left
                for w in player.robot.weapons.values()
            }
        )
        
        try:
            if player.keys.q and not player.old_keys.q:
                player.robot.ability_func(1, new_commands, info)
            elif player.keys.w and not player.old_keys.w:
                player.robot.ability_func(2, new_commands, info)
            elif player.keys.e and not player.old_keys.e:
                player.robot.ability_func(3, new_commands, info)
            elif player.keys.a and not player.old_keys.a:
                player.robot.ability_func(4, new_commands, info)
            elif player.keys.s and not player.old_keys.s:
                player.robot.ability_func(5, new_commands, info)
            elif player.keys.d and not player.old_keys.d:
                player.robot.ability_func(6, new_commands, info)
                
            if len(new_commands) > 0:
                new_commands = list(filter(lambda c: c.id in player.robot.weapons , new_commands))
                
                for command in new_commands:
                    command.time = datetime.now()
                    
                total_energy_cost = calculate_ability_energy_cost(player.robot, new_commands)
                    
                if self._can_activate_ability(player, new_commands) and total_energy_cost <= player.robot.energy:
                    player.robot.energy -= total_energy_cost
                    fired_weapons = set([c.id for c in new_commands])
                    for weapon_id in fired_weapons:
                        player.robot.weapons[weapon_id].cooldown_time_left = player.robot.weapons[weapon_id].stats.cooldown_seconds
                        
                    self.player_commands[player.idx] += new_commands
        except:
            pass
            
    def _can_activate_ability(self, player: PlayerInstance, commands: list[WeaponCommand]):
        for weapon_id in set([c.id for c in commands]):
            if player.robot.weapons[weapon_id].cooldown_time_left > 0:
                return False
            
        return True
            
    def _update_player(self, player: PlayerInstance, delta: timedelta):
        player.robot.energy = min(player.robot.max_energy, player.robot.energy + player.robot.energy_regen)
        
        completed: list[WeaponCommand] = []
        for command in self.player_commands[player.idx]:
            if command.time + command.delay < datetime.now():
                completed.append(command)
                weapon = player.robot.weapons[command.id]
                sx, sy = calculate_weapon_point_offset((player.robot.x, player.robot.y), player.robot.angle, (weapon.x, weapon.y), weapon.angle, (7.5, 0))
                p_angle = player.robot.angle + weapon.angle
                
                self.projectiles.append(Projectile(self.projectile_id_counter, player.idx, sx, sy, p_angle, weapon.stats.bullet_size, weapon.stats.bullet_speed, weapon.stats.base_damage))
                self.projectile_id_counter = (self.projectile_id_counter + 1) % 65000
                
        for completed_command in completed:
            self.player_commands[player.idx].remove(completed_command)
            
        for weapon in player.robot.weapons.values():
            weapon.cooldown_time_left = max(0, weapon.cooldown_time_left - delta.total_seconds())
            
    def _update_projectile(self, projectile: Projectile):
        projectile.x += projectile.speed * math.cos(projectile.angle)
        projectile.y += projectile.speed * math.sin(projectile.angle)
        
        self.spatial_grid.add_to_grid((projectile.x, projectile.y), projectile)
            
    def _is_outside_screen(self, projectile: Projectile):
        return projectile.x < -projectile.size or projectile.x > self.arena.width + projectile.size or projectile.y < -projectile.size or projectile.y > self.arena.height + projectile.size
            
    def _check_collisions(self):
        for player in self._alive_players():
            bounding_box_corners = self._get_player_bounding_box(player)
            bounding_box_grid_coords = set([self.spatial_grid.get_grid_coord(pos) for pos in bounding_box_corners])
            
            for grid_coord in bounding_box_grid_coords:
                for projectile in self.spatial_grid.get_bullets_in_grid_cell(grid_coord):
                    if projectile.destroy:
                        continue
                    
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
                
            
    def _get_player_bounding_box(self, player: PlayerInstance) -> list[tuple[float, float]]:
        return [
            (player.robot.x - player.robot.size, player.robot.y - player.robot.size),
            (player.robot.x + player.robot.size, player.robot.y - player.robot.size),
            (player.robot.x - player.robot.size, player.robot.y + player.robot.size),
            (player.robot.x + player.robot.size, player.robot.y + player.robot.size)
        ]
            
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
                projectile.id,
                projectile.x,
                projectile.y,
                projectile.angle,
                projectile.size
            )
            for projectile in self.projectiles
        ]
        
        return state
        
    def get_robot_state(self, id: str) -> dict:
        player = self.players[id]
        return player.robot.interface.get_state()
        
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
        