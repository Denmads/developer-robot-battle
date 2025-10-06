from dataclasses import dataclass


@dataclass
class Arena:
    width: int
    height: int
    player_starting_dist: int
    
    @staticmethod
    def create(num_players: int) -> "Arena":
        width = 800
        height = 600
        dist_from_middle = 200
        
        if num_players > 4:
            width += ((num_players - 4) // 2) * 100
            height += ((num_players - 4) // 2) * 75
            dist_from_middle += ((num_players - 4) // 2) * 25
            
        return Arena(width, height, dist_from_middle)