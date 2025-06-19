import cProfile

from pygame import Vector2
from vi import Agent, HeadlessSimulation, Simulation
from dataclasses import dataclass
from vi.config import Config, dataclass
import sys, os, random
from map_design import obstacle_size, grid, build
random.seed(13)
import datetime
from polars import DataFrame

random.seed(13)

@dataclass
class PredPreyConfig(Config):
    movement_speed: float = 5.0
    radius: int = 10
    image_rotation: bool = False
    fps_limit: int = 120
    duration: int = 100 * 60
    seed: int = 13
    rabbit_lifespan: int = 1000
    fox_hunger: int = 1000

    


class Rabbit(Agent[PredPreyConfig]):
    
    #initial lifespan and random movement direction
    def on_spawn(self,speed=1):
        self.lifespan = self.config.rabbit_lifespan
        angle = random.uniform(0, 360)
        self.move = Vector2(speed, 0).rotate(angle)
        self.pos = Vector2(random.randint(4,12)* obstacle_size, random.randint(4,12)* obstacle_size)

    def update(self):
        #lifespan decreases each tick, death when lifespan=0
        
        self.lifespan -= 1

        if self.lifespan <= 0:
            self.kill()
            return
        self.change_position()
        
        #reproduction with a probability of 0.001 (asexual)
        if self.shared.prng_move.random() < 0.001: 
            self.reproduce()


class Fox(Agent[PredPreyConfig]):

    #initial hunger and movement direction
    def on_spawn(self):
        self.hunger = 0
        angle = random.uniform(0, 360)
        self.move = Vector2(1, 0).rotate(angle)
        self.pos = Vector2(random.randint(18,26)* obstacle_size, random.randint(18,26)* obstacle_size)

    
    def update(self):
        self.change_position()
        ate = False

        # Look for a rabbit in proximity
        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit):
                other.kill()
                ate = True
                break  # Stop after first one eaten

        if ate:
            self.hunger = 0
            self.reproduce()
        else:
            self.hunger += 1

        if self.hunger >= self.config.fox_hunger:
            self.kill()

map_design = (sys.argv[1] if len(sys.argv) > 1
       else os.getenv("MAP_DESIGN", "corridor"))

cfg = PredPreyConfig(seed=13)
cfg.window.width = cfg.window.height = obstacle_size * grid
sim = Simulation(cfg)
build(sim, map_design)

rng = random.Random(cfg.seed)
ri  = lambda a, b: rng.randint(a, b) * obstacle_size

# Spawing the animals in their nests 
sim.batch_spawn_agents(20, Rabbit, images=["images/rabbit.png"])
sim.batch_spawn_agents(20, Fox, images=["images/fox.png"])

df: DataFrame = sim.run().snapshots
time_label = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
df.write_csv('snapshot')