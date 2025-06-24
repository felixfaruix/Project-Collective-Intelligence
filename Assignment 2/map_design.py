from vi import Simulation
from pygame import Vector2

obstacle_size = 24
grid = 30
window_size = obstacle_size * grid
obstacle_image = "images/obstacle.png"
walkable_grid = [[False for _ in range(grid)] for _ in range(grid)]

def wall_builder(sim, r, c):
    sim.spawn_obstacle(obstacle_image, c * obstacle_size, r * obstacle_size)

def structured_map(sim: Simulation):
    global walkable_grid
    walkable_grid = [[False for _ in range(grid)] for _ in range(grid)]

    for r in range(grid):
        for c in range(grid):
            
            zone_rabbit_male   = 2 <= r <= 5 and 2 <= c <= 5
            zone_rabbit_female = 2 <= r <= 5 and 24 <= c <= 27
            zone_fox_male      = 24 <= r <= 27 and 2 <= c <= 5
            zone_fox_female    = 24 <= r <= 27 and 24 <= c <= 27

            
            corridor_rabbit_male   = 2 <= r <= 4 and 6 <= c <= 12
            corridor_rabbit_female = 2 <= r <= 4 and 17 <= c <= 23
            corridor_fox_male      = 24 <= r <= 26 and 6 <= c <= 12
            corridor_fox_female    = 24 <= r <= 26 and 17 <= c <= 23

            
            vertical_corridor = 11 <= r <= 18 and 13 <= c <= 15

            
            rabbit_to_center_left  = 5 <= r <= 10 and 10 <= c <= 12
            rabbit_to_center_right = 5 <= r <= 10 and 17 <= c <= 19
            fox_to_center_left     = 19 <= r <= 23 and 10 <= c <= 12
            fox_to_center_right    = 19 <= r <= 23 and 17 <= c <= 19

            
            central_open = 11 <= r <= 18 and 10 <= c <= 19

            walkable = (
                zone_rabbit_male or zone_rabbit_female or
                zone_fox_male or zone_fox_female or
                corridor_rabbit_male or corridor_rabbit_female or
                corridor_fox_male or corridor_fox_female or
                vertical_corridor or
                rabbit_to_center_left or rabbit_to_center_right or
                fox_to_center_left or fox_to_center_right or
                central_open
            )

            if walkable:
                walkable_grid[r][c] = True
            else:
                wall_builder(sim, r, c)


def corridor(sim: Simulation):
    for r in range(grid):
        for c in range(grid):
            zone_rabbit_male   = 3 <= r <= 6 and 3 <= c <= 6
            zone_rabbit_female = 3 <= r <= 6 and 23 <= c <= 26
            zone_fox_male      = 23 <= r <= 26 and 3 <= c <= 6
            zone_fox_female    = 23 <= r <= 26 and 23 <= c <= 26

            corridor_rabbit_male   = 4 <= r <= 5 and 7 <= c <= 13
            corridor_rabbit_female = 4 <= r <= 5 and 16 <= c <= 22
            corridor_fox_male      = 24 <= r <= 25 and 7 <= c <= 13
            corridor_fox_female    = 24 <= r <= 25 and 16 <= c <= 22
            central_corridor       = 5 <= r <= 24 and 13 <= c <= 16

            walkable_path = (
                zone_rabbit_male or zone_rabbit_female or
                zone_fox_male or zone_fox_female or
                corridor_rabbit_male or corridor_rabbit_female or
                corridor_fox_male or corridor_fox_female or
                central_corridor
            )

            if not walkable_path:
                wall_builder(sim, r, c)
            else:
                walkable_grid[r][c] = True

def open(sim):
    for r in range(grid):
        for c in range(grid):
            if r in (0, grid-1) or c in (0, grid-1):
                wall_builder(sim, r, c)

shift_map = {"open": open, "corridor": corridor, "structured": structured_map}

def build(sim, name: str):
    if name not in shift_map:
        raise ValueError(f"Unknown map '{name}'. Options: {list(shift_map)}")
    shift_map[name](sim)

def is_walkable_at(pos: Vector2) -> bool:
    row = int(pos.y // obstacle_size)
    col = int(pos.x // obstacle_size)
    return (
        0 <= row < grid and
        0 <= col < grid and
        walkable_grid[row][col]
    )

def print_walkable_grid():
    for r in range(grid):
        print("".join("." if walkable_grid[r][c] else "#" for c in range(grid)))
