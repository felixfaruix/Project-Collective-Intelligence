from vi import Simulation, Config, HeadlessSimulation

obstacle_size = 24
grid = 30
window_size = obstacle_size * grid
obstacle_image = "images/obstacle.png"


def wall_builder (sim, r, c):
    sim.spawn_obstacle(obstacle_image, c*obstacle_size, r*obstacle_size)

def open(sim):
    """Border walls only."""
    for r in range(grid):
        for c in range(grid):
            if r in (0, grid-1) or c in (0, grid-1):
                wall_builder(sim, r, c)

def corridor(sim: Simulation):
    for r in range(grid):
        for c in range(grid):

            # Two different zonas for the nests
            zone_a =  2 <= r <= 13 and  2 <= c <= 13
            zone_b = 17 <= r <= 28 and 17 <= c <= 28

            corridor_upper =  6 <= r <=  8 and 13 < c <= 23
            corridor_upper_dow =  8 < r <= 22 and 21 <= c <= 23

            # Lower horizontal corridor
            corridor_lower = 22 <= r <= 24 and  6 <= c <= 17
            corridor_lower_up = 13 <= r <= 22 and  6 <= c <=  8

            walkable_path = (zone_a or zone_b or
                corridor_upper or corridor_upper_dow or
                corridor_lower or corridor_lower_up)
    
            if not walkable_path:
                wall_builder(sim, r, c)


shift_map = {"open": open, "corridor": corridor}

def build(sim, name: str):
    if name not in shift_map:
        raise ValueError(f"Unknown map '{name}'. Options: {list(shift_map)}")
    shift_map[name](sim)