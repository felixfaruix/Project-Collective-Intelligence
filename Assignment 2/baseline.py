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
        self.save_data("Kind", "Rabbit")
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
        self.save_data("Kind", "Fox")
        
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

def run_simulation(seed: int) -> pl.DataFrame:
    # build a fresh config per seed
    cfg = PredPreyConfig(seed=seed)
    cfg.window.width = cfg.window.height = obstacle_size * grid

    sim = HeadlessSimulation(cfg)           # head-less, no window[1]
    build(sim, map_design)

    # spawn agents
    sim.batch_spawn_agents(20, Rabbit, ["images/rabbit.png"])
    sim.batch_spawn_agents(20, Fox,    ["images/fox.png"])

    # run and return the snapshot dataframe
    df = sim.run().snapshots
    # keep the seed so we know which row came from which run
    return df.with_columns(pl.lit(seed).alias("seed"))


if __name__ == "__main__":
    # create a list of random seeds – here 8, change as desired
    seeds = [random.randint(0, 1_000_000) for _ in range(20)]

    # run the simulations in parallel (one core per process)
    with Pool() as pool:                    # multiprocessing.Pool[1]
        dfs = pool.map(run_simulation, seeds)

    # concatenate all runs into one big table
    df_all = pl.concat(dfs)

    # save with timestamp
    time_label = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    df_all.write_csv(f"snapshots_{time_label}.csv")