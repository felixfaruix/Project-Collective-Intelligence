from dataclasses import dataclass
from pygame import Vector2
from vi import Agent, Config, Simulation
from vi.util import count
import random

random.seed(69)

@dataclass
class CockroachConfig(Config):
    some_weight = 0



class Cockroach(Agent[CockroachConfig]):

    def __init__(self, images, simulation, pos = None, move = None):
        super().__init__(images, simulation, pos, move)

    def change_position(self):
        self.there_is_no_escape()

        self.pos += self.move
        
        

config = Config()
x, y = config.window.as_tuple()

(
    Simulation(
        Config(image_rotation=True, movement_speed=1, radius=50, fps_limit=60, seed=69, duration=100*60)
    )
    .spawn_site("images/site.png", x=375, y=375)
    .batch_spawn_agents(100, Cockroach, images=["images/dot.png"])
    .run()
)