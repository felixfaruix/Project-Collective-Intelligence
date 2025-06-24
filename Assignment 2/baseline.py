import cProfile
from multiprocessing import Pool

from pygame import Vector2
from vi import Agent, HeadlessSimulation, Simulation
from dataclasses import dataclass
from vi.config import Config, dataclass
import sys, os, random
from map_design import obstacle_size, grid, build
random.seed(13)
from datetime import datetime
import polars as pl

random.seed(13)

@dataclass
class PredPreyConfig(Config):
    v_min: float = 1.0
    v_max: float = 3.0
    radius: int = 10
    image_rotation: bool = False
    fps_limit: int = 60
    duration: int = 100 * 60
    seed: int = 13
    rabbit_lifespan: int = 200
    fox_lifespan: int = 200
    fox_food_gain: int = 50

nest_top_left = [(x, y) for x in range(1, 3) for y in range(1, 3)]
nest_top_right = [(x, y) for x in range(grid - 3, grid - 1) for y in range(1, 3)]
nest_bottom_left = [(x, y) for x in range(1, 3) for y in range(grid - 3, grid - 1)]
nest_bottom_right = [(x, y) for x in range(grid - 3, grid - 1) for y in range(grid - 3, grid - 1)]
all_nests = nest_top_left + nest_top_right + nest_bottom_left + nest_bottom_right

class Rabbit(Agent[PredPreyConfig]):

    def on_spawn(self, speed=1):
        self.max_lifespan = self.config.rabbit_lifespan
        self.lifespan = self.max_lifespan
        angle = random.uniform(0, 360)
        self.move = Vector2(speed, 0).rotate(angle)
        tile_x, tile_y = random.choice(all_nests)
        self.pos = Vector2(tile_x * obstacle_size, tile_y * obstacle_size)
        self.sex = random.choice(["M", "F"])
        self.save_data("Sex", self.sex)

    def update(self):
        self.save_data("Kind", "Rabbit")
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        speed = self.config.v_min + (1 - (self.lifespan / self.max_lifespan)) * (self.config.v_max - self.config.v_min)
        print(f"Rabbit {self.id} | Lifespan: {self.lifespan} | Speed: {speed:.2f}")

        if self.move.length() > 0:
            self.move = self.move.normalize() * speed

        self.change_position()

        # Exponentially increasing reproduction probability based on urgency
        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit) and other.sex != self.sex:
                if self.pos.distance_to(other.pos) == 0:
                    urgency = 1 - (self.lifespan / self.max_lifespan)
                    prob = urgency ** 2  # exponential increase
                    if self.shared.prng_move.random() < prob:
                        self.reproduce()
                    break

class Fox(Agent[PredPreyConfig]):

    def on_spawn(self):
        self.max_lifespan = self.config.fox_lifespan
        self.lifespan = self.max_lifespan
        angle = random.uniform(0, 360)
        self.move = Vector2(1, 0).rotate(angle)
        tile_x, tile_y = random.choice(all_nests)
        self.pos = Vector2(tile_x * obstacle_size, tile_y * obstacle_size)
        self.sex = random.choice(["M", "F"])
        self.save_data("Sex", self.sex)

    def update(self):
        self.save_data("Kind", "Fox")
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        speed = self.config.v_min + (1 - (self.lifespan / self.max_lifespan)) * (self.config.v_max - self.config.v_min)
        if self.move.length() > 0:
            self.move = self.move.normalize() * speed

        self.change_position()

        # Eat rabbits if on the same tile
        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit):
                other.kill()
                self.lifespan = min(self.lifespan + self.config.fox_food_gain, self.max_lifespan)
                break

        # Sexual reproduction (independent of eating)
        for other in self.in_proximity_performance():
            if isinstance(other, Fox) and other.sex != self.sex:
                if self.pos.distance_to(other.pos) == 0:
                    urgency = 1 - (self.lifespan / self.max_lifespan)
                    prob = urgency ** 2  # exponential increase
                    if self.shared.prng_move.random() < prob:
                        self.reproduce()
                    break

map_design = (sys.argv[1] if len(sys.argv) > 1
    else os.getenv("MAP_DESIGN", "corridor"))

if __name__ == "__main__":
    cfg = PredPreyConfig(seed=13)
    cfg.window.width = cfg.window.height = obstacle_size * grid
    sim = Simulation(cfg)
    build(sim, "corridor")
    sim.batch_spawn_agents(20, Rabbit, images=["images/rabbit.png"])
    sim.batch_spawn_agents(20, Fox, images=["images/fox.png"])
    sim.run()

