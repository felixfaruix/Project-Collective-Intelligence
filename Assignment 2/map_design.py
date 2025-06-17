from vi import Simulation, Config

obstacle_size = 24
grid = 30
window_size = obstacle_size * grid
obstacle_image= "images/obstacle.png"


def build_dual_corridors(sim: Simulation):
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
                sim.spawn_obstacle(obstacle_image, c * obstacle_size, r *obstacle_size)

if __name__ == "__main__":

    cfg = Config()
    cfg.window.width = cfg.window.height = window_size
    sim = Simulation(cfg)
    build_dual_corridors(sim)
    sim.run()