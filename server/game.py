from dataclasses import dataclass, field
import math
from time import sleep
from typing import Callable

import pygame
from common.game_state import GameState, PlayerState, ProjectileState
from common.projectile import Projectile
from common.robot import Robot
from common.constants import ARENA_HEIGHT, ARENA_WIDTH, ROBOT_RADIUS
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
    
    # keys
    old_keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)
    keys: PlayerKeyState = field(init=False, default_factory=PlayerKeyState)

class Game:
    
    def __init__(self, players: list[Player], send_state: Callable[[GameState], None]):
        angle_step = math.pi * 2 / len(players)
        starting_dist_from_middle = 200
        middle_x = ARENA_WIDTH / 2
        middle_y = ARENA_HEIGHT / 2
        
        [x.robot.create_robot() for x in players]
        
        self.players: dict[str, PlayerInstance] = { x.id: PlayerInstance(
            i,
            Robot(
                middle_x + starting_dist_from_middle * math.cos(angle_step * i), 
                middle_y + starting_dist_from_middle * math.sin(angle_step * i),
                angle_step * i + math.pi, 
                x.robot.do_ability)) 
            for i, x in enumerate(players)
            }
        
        self.projectiles: list[Projectile] = []
        
        self.running = False
        self.send_state = send_state
        
    def run(self):
        self.running = True
        while self.running:
            for player in self.players.values():
                
                self._update_movement(player)
                
                player.old_keys = player.keys.clone()
                
            for projectile in self.projectiles:
                self._update_projectile(projectile)
                
            for p in list(filter(self._is_outside_screen, self.projectiles)):
                p.destroy = True
            self._check_collisions()
            
            self.projectiles = list(filter(lambda p: not p.destroy, self.projectiles))
                
            self.send_state(self.get_state())
            sleep(1 / 20) # 20 updates per second
        
    def _update_movement(self, player: PlayerInstance):
        robot_move_speed = 5
        robot_turn_speed = 0.1
        
        if player.keys.left:
            player.robot.angle -= robot_turn_speed
        if player.keys.right:
            player.robot.angle += robot_turn_speed
        
        dx = robot_move_speed * math.cos(player.robot.angle)
        dy = robot_move_speed * math.sin(player.robot.angle)
        
        if player.keys.up:
            player.robot.x += dx
            player.robot.y += dy
        if player.keys.down:
            player.robot.x -= dx
            player.robot.y -= dy
            
        if player.keys.q and not player.old_keys.q:
            sx = player.robot.x + robot_move_speed * math.cos(player.robot.angle)
            sy = player.robot.y + robot_move_speed * math.sin(player.robot.angle)
            self.projectiles.append(Projectile(player.idx, sx, sy, player.robot.angle, 3, 10, 5))
            
    def _update_projectile(self, projectile: Projectile):
        projectile.x += projectile.speed * math.cos(projectile.angle)
        projectile.y += projectile.speed * math.sin(projectile.angle)
            
    def _is_outside_screen(self, projectile: Projectile):
        return projectile.x < -projectile.size or projectile.x > ARENA_WIDTH + projectile.size or projectile.y < -projectile.size or projectile.y > ARENA_HEIGHT + projectile.size
            
    def _check_collisions(self):
        robot_radius_2 = ROBOT_RADIUS * ROBOT_RADIUS
        for projectile in self.projectiles:
            if projectile.destroy:
                continue
            
            for player in self.players.values():
                if player.idx == projectile.owner_idx:
                    continue
                
                euclidean_dist = abs(player.robot.x - projectile.x) + abs(player.robot.y - projectile.y)
                
                if euclidean_dist < ROBOT_RADIUS * 2:
                    dist = math.pow(player.robot.x - projectile.x, 2) + math.pow(player.robot.y - projectile.y, 2)
                    if dist < robot_radius_2:
                        projectile.destroy = True
                        player.robot.hp -= projectile.damage
            
    def get_state(self) -> GameState:
        state = GameState()
        
        state.players = [
            PlayerState(
                player.idx,
                player.robot.x,
                player.robot.y,
                player.robot.angle,
                player.robot.hp
            ) 
            for player in self.players.values()
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
        