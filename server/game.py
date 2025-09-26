from dataclasses import dataclass, field
import math
from time import sleep
from typing import Callable

import pygame
from common.game_state import GameState, PlayerState
from common.robot import Robot
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
                angle_step * i, 
                x.robot.do_ability)) 
            for i, x in enumerate(players)
            }
        
        self.running = False
        self.send_state = send_state
        
    def run(self):
        self.running = True
        while self.running:
            for player in self.players.values():
                
                self._update_movement(player)
                
                player.old_keys = player.keys
                
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
        
        return state
        
    def stop(self):
        self.running = False
        