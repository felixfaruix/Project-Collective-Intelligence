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
    fox_food_gain: int = 50   # regaining lifespan when they eat

    


class Rabbit(Agent[PredPreyConfig]):
    
    
    #initial lifespan and random movement direction
    def on_spawn(self,speed=1):
        self.max_lifespan = self.config.rabbit_lifespan
        self.lifespan = self.max_lifespan

        angle = random.uniform(0, 360)
        self.move = Vector2(speed, 0).rotate(angle)
        self.pos = Vector2(random.randint(4,12)* obstacle_size, random.randint(4,12)* obstacle_size)

    def update(self):
        self.save_data("Kind", "Rabbit")
        #lifespan decreases each tick, death when lifespan=0
        
        self.lifespan -= 1

        if self.lifespan <= 0:
            self.kill()
            return
        
        #formula as in team mario doc
        speed = self.config.v_min + (1 - (self.lifespan / self.max_lifespan)) * (self.config.v_max - self.config.v_min)
        print(f"Rabbit {self.id} | Lifespan: {self.lifespan} | Speed: {speed:.2f}")

        if self.move.length() > 0:
            self.move = self.move.normalize() * speed

        self.change_position()
    
        #reproduction with a probability of 0.001 (asexual)
        if self.shared.prng_move.random() < 0.001: 
            self.reproduce()
            
        


class Fox(Agent[PredPreyConfig]):

    #initial hunger and movement direction
    def on_spawn(self):
        
        self.max_lifespan = self.config.fox_lifespan
        self.lifespan = self.max_lifespan

        angle = random.uniform(0, 360)
        self.move = Vector2(1, 0).rotate(angle)
        self.pos = Vector2(random.randint(18,26)* obstacle_size, random.randint(18,26)* obstacle_size)

    

    def update(self):
        self.save_data("Kind", "Fox")
        #age by one tick
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        #compute urgency-driven speed
        speed = self.config.v_min + (1 - (self.lifespan / self.max_lifespan)) * (self.config.v_max - self.config.v_min)

        if self.move.length() > 0:
            self.move = self.move.normalize() * speed

        # Move and attempt to eat
        self.change_position()
        ate = False
        for other, dist in self.in_proximity_accuracy():
            if isinstance(other, Rabbit) and dist == 0:
                other.kill()
                ate = True
                break

        if ate:
            # Regain lifespan up to max and reproduce
            self.lifespan = min(self.lifespan + self.config.fox_food_gain, self.max_lifespan)
            self.reproduce()

        

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

