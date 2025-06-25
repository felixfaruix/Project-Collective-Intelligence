import cProfile
from multiprocessing import Pool
from pygame import Vector2
from vi import Agent, HeadlessSimulation, Simulation
from dataclasses import dataclass
from vi.config import Config, dataclass
import sys, os, random
from map_design import OB as obstacle_size, GRID as grid, build, nest_top_left as RABBIT_F_NESTS, nest_bottom_right as RABBIT_M_NESTS, nest_bottom_left as FOX_M_NESTS, nest_top_right as FOX_F_NESTS, all_nests
from datetime import datetime
from datetime import datetime
import polars as pl

random.seed(13)

def age_to_speed(v_min, v_max, age, max_age):
    urgency = 1 - (age / max_age)
    return v_min + (urgency ** 2) * (v_max - v_min)

def make_rabbit(sex: str, pool):
    class R(Rabbit):
        fixed_sex = sex
        spawn_pool = pool
    return R

def make_fox(sex: str, pool):
    class F(Fox):
        fixed_sex = sex
        spawn_pool = pool
    return F

@dataclass
class PredPreyConfig(Config):
    v_min: float = 1.0
    v_max: float = 3.0
    radius: int = 10
    image_rotation: bool = False
    fps_limit: int = 60
    duration: int = 100 * 60
    seed: int = 13
    rabbit_lifespan: int = 2000
    fox_lifespan: int = 1000
    fox_food_gain: int = 50

class Rabbit(Agent[PredPreyConfig]):
    fixed_sex = None
    spawn_pool = []

    def on_spawn(self, speed=1):
        r, c = random.choice(self.spawn_pool)
        self.sex = self.fixed_sex
        self.pos = Vector2(c * obstacle_size, r * obstacle_size)
        self.max_lifespan = self.config.rabbit_lifespan
        self.lifespan = self.max_lifespan
        self.move = Vector2(1, 0).rotate(random.uniform(0, 360))
        self._still_stuck = False

    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        speed = age_to_speed(self.config.v_min, self.config.v_max, self.lifespan, self.max_lifespan)
        if self.move.length() > 0:
            self.move = self.move.normalize() * speed
        self.change_position()

        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit) and other.sex != self.sex:
                if self.pos.distance_to(other.pos) == 0:
                    urgency = 1 - (self.lifespan / self.max_lifespan)
                    prob = urgency ** 2
                    if self.shared.prng_move.random() < prob:
                        self.reproduce()
                    break

class Fox(Agent[PredPreyConfig]):
    fixed_sex = None
    spawn_pool = []

    def on_spawn(self):
        r, c = random.choice(self.spawn_pool)
        self.sex = self.fixed_sex
        self.pos = Vector2(c * obstacle_size, r * obstacle_size)
        self.max_lifespan = self.config.fox_lifespan
        self.lifespan = self.max_lifespan
        self.move = Vector2(1, 0).rotate(random.uniform(0, 360))
        self._still_stuck = False

    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        speed = age_to_speed(self.config.v_min, self.config.v_max, self.lifespan, self.max_lifespan)
        if self.move.length() > 0:
            self.move = self.move.normalize() * speed
        self.change_position()

        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit):
                other.kill()
                self.lifespan = min(self.lifespan + self.config.fox_food_gain, self.max_lifespan)
                break

        for other in self.in_proximity_performance():
            if isinstance(other, Fox) and other.sex != self.sex:
                if self.pos.distance_to(other.pos) == 0:
                    urgency = 1 - (self.lifespan / self.max_lifespan)
                    prob = urgency ** 2
                    if self.shared.prng_move.random() < prob:
                        self.reproduce()
                    break

if __name__ == "__main__":
    cfg = PredPreyConfig(seed=13)
    cfg.window.width = cfg.window.height = obstacle_size * grid
    sim = Simulation(cfg)
    build(sim, "corridor")

    sim.batch_spawn_agents(20, make_rabbit("F", RABBIT_F_NESTS), images=["images/rabbit.png"])
    sim.batch_spawn_agents(20, make_rabbit("M", RABBIT_M_NESTS), images=["images/rabbit.png"])
    sim.batch_spawn_agents(20, make_fox("M", FOX_M_NESTS), images=["images/fox.png"])
    sim.batch_spawn_agents(20, make_fox("F", FOX_F_NESTS), images=["images/fox.png"])

    sim.run()
