from collections import defaultdict
import math

from common.robot import Robot
from common.weapon import WeaponCommand

def rot(vx, vy, a):
    cs = math.cos(a)
    sn = math.sin(a)
    return vx * cs - vy * sn, vx * sn + vy * cs

def calculate_weapon_point_offset(
    player_pos: tuple[float, float], 
    player_angle: float, 
    weapon_offset: tuple[float, float], 
    weapon_angle: float, 
    point_offset: tuple[float, float]
    )-> tuple[float, float]:
    
        wo_rx, wo_ry = rot(weapon_offset[0], weapon_offset[1], player_angle)
        
        weapon_base_x = player_pos[0] + wo_rx
        weapon_base_y = player_pos[1] + wo_ry
        
        cs = math.cos(player_angle + weapon_angle)
        sn = math.sin(player_angle + weapon_angle)
        
        return (
            point_offset[0] * cs - point_offset[1] * sn + weapon_base_x,
            point_offset[0] * sn + point_offset[1] * cs + weapon_base_y
        )
        
def calculate_energy_cost(robot: Robot, commands: list[WeaponCommand]) -> float:
    weapon_fire_counts: defaultdict[str, int] = defaultdict(int)
    for command in commands:
        weapon_fire_counts[command.id] += 1
        
    energy_cost = 0
    for weapon_id, fire_count in weapon_fire_counts.items():
        weapon_stats = robot.weapons[weapon_id].stats
        energy_cost += weapon_stats.base_energy_cost * math.pow(weapon_stats.consecutive_energy_cost_factor, fire_count - 1)
        
    return energy_cost