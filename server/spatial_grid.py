from common.projectile import Projectile


class SpatialGrid:
    
    def __init__(self, cell_width: int, cell_height: int = None):
        self.cell_width = cell_width
        self.cell_height = cell_width if cell_height is None else cell_height
        
        self.grid: dict[tuple[int, int], list[Projectile]] = {}
        
    def add_to_grid(self, pos: tuple[float, float], bullet: Projectile):
        grid_pos = self.get_grid_coord(pos)
        if grid_pos not in self.grid:
            self.grid[grid_pos] = []
        self.grid[grid_pos].append(bullet)
    
    def get_bullets_in_grid_cell(self, pos: tuple[float, float]) -> list[Projectile]:
        if pos in self.grid:
            return self.grid[pos]
        return []
    
    def clear(self):
        self.grid = {}
    
    def get_grid_coord(self, pos: tuple[float, float]):
        return (
            pos[0] // self.cell_width,
            pos[1] // self.cell_height
        )
        
    