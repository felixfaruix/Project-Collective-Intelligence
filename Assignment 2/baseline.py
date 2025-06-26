# baseline.py
# Complete, self-contained simulation script.
#  • Writes metrics every frame (no ShapeError)
#  • Stops automatically the moment the last real agent dies
#  • Produces <base>.parquet  +  <base>.json per run

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import polars as pl
from pygame import Vector2
from vi import Agent
from vi.config import Config, dataclass
from vi.simulation import Simulation as _Sim, HeadlessSimulation as _HSim

# ────────────────────────────────────────────────────────────
# Auto-stopping versions of Violet’s Simulation classes
# ────────────────────────────────────────────────────────────
class _AutoStopMixin:
    """Stop the simulation right after the first tick that leaves zero agents."""
    def tick(self):                            # type: ignore[override]
        super().tick()                         # call the parent tick
        if not self._agents:                   # nobody left alive?
            self.stop()                        # abort before next empty frame

class Simulation(_AutoStopMixin, _Sim):
    pass

class HeadlessSimulation(_AutoStopMixin, _HSim):
    pass

# ────────────────────────────────────────────────────────────
# Map / scenario helpers (unchanged)
# ────────────────────────────────────────────────────────────
from map_design import (
    build,
    OB as CELL, GRID,
    NEST, tl, br,
    all_nests,
    nest_top_left     as RABBIT_F_NESTS,
    nest_bottom_right as RABBIT_M_NESTS,
    nest_bottom_left  as FOX_M_NESTS,
    nest_top_right    as FOX_F_NESTS,
)

NEST_IMG  = "images/rabbit_nest.png"
GRASS_IMG = "images/grass.png"

rabbit_nest_site_ids: list[int] = []
grass_site_ids:  list[int] = []

# ────────────────────────────────────────────────────────────
# Config
# ────────────────────────────────────────────────────────────
@dataclass
class PredPreyConfig(Config):
    v_min: float = 1.0
    v_max: float = 3.0
    radius: int  = 10
    image_rotation: bool = False
    fps_limit: int = 60
    duration: int = 100 * 60
    seed: int = 13
    rabbit_lifespan: int = 2000
    fox_lifespan:    int = 1000
    fox_food_gain:   int = 50
    rabbit_food_gain:int = 20

# ────────────────────────────────────────────────────────────
# Utility / geometry functions
# ────────────────────────────────────────────────────────────
def on_rabbit_nest(agent) -> bool:
    sid = agent.on_site_id()
    return sid is not None and sid in rabbit_nest_site_ids

def on_grass(agent) -> bool:
    sid = agent.on_site_id()
    return sid is not None and sid in grass_site_ids

def age_to_speed(vmin, vmax, life_left, max_life):
    u = 1 - life_left / max_life
    return vmin + (u ** 2) * (vmax - vmin)

def spawn_sites(sim):
    rabbit_nest_site_ids.clear()
    grass_site_ids.clear()
    half = NEST / 2
    # two nests
    for corner in (tl, br):
        p = Vector2((corner + half) * CELL, (corner + half) * CELL)
        sim.spawn_site(NEST_IMG,  x=int(p.x)-12, y=int(p.y)-12)
        rabbit_nest_site_ids.append(sim._sites.sprites()[-1].id)
    # two grass on same corners
    for corner in (tl, br):
        p = Vector2((corner + half) * CELL, (corner + half) * CELL)
        sim.spawn_site(GRASS_IMG, x=int(p.x)-12, y=int(p.y)-12)
        grass_site_ids.append(sim._sites.sprites()[-1].id)
    # four grass near centre
    mid = GRID // 2
    for dx in (0, -1):
        for dy in (0, -1):
            p = Vector2((mid + dx) * CELL, (mid + dy) * CELL)
            sim.spawn_site(GRASS_IMG, x=int(p.x), y=int(p.y))
            grass_site_ids.append(sim._sites.sprites()[-1].id)

NEST_CELLS = set(all_nests)
RABBIT_NEST_CELLS = {
    (r, c) for r in range(tl, tl + NEST) for c in range(tl, tl + NEST)
}.union({
    (r, c) for r in range(br, br + NEST) for c in range(br, br + NEST)
})
def inside_rabbit_nest_cell(pos: Vector2) -> bool:
    r, c = int(pos.y // CELL), int(pos.x // CELL)
    return (r, c) in RABBIT_NEST_CELLS

HOME_FACTOR = 25
FAR_CELLS   = 15
TL_CENTER   = Vector2((tl + NEST/2)*CELL, (tl + NEST/2)*CELL)
BR_CENTER   = Vector2((br + NEST/2)*CELL, (br + NEST/2)*CELL)

# ────────────────────────────────────────────────────────────
# Agent classes with per-tick metric logging (unchanged)
# ────────────────────────────────────────────────────────────
class Rabbit(Agent[PredPreyConfig]):
    fixed_sex  = None
    spawn_pool = []
    def on_spawn(self):
        r, c = random.choice(self.spawn_pool)
        self.pos = Vector2(c*CELL, r*CELL)
        self.sex = self.fixed_sex
        self.max_life = self.config.rabbit_lifespan
        self.life     = self.max_life
        self.move     = Vector2(1,0).rotate(random.uniform(0,360))
        self.home_center = TL_CENTER if self.sex=="F" else BR_CENTER
        self.go_home  = False
    # behaviour helpers
    def _steer(self):
        if self.go_home:
            if on_rabbit_nest(self):
                self.go_home = False
            else:
                v = self.home_center - self.pos
                if v.length(): self.move = v.normalize()
        elif random.random() < 0.05:
            self.move = self.move.rotate(random.uniform(-45,45))
    def _decide(self):
        d = self.pos.distance_to(self.home_center)/CELL
        if self.life > d*HOME_FACTOR or d >= FAR_CELLS:
            self.go_home = True
    # update
    def update(self):
        self.life -= 1
        if self.life <= 0:
            self._log(kill=0, mated=0)
            self.kill(); return
        self._steer()
        speed = age_to_speed(self.config.v_min, self.config.v_max,
                             self.life, self.max_life)
        if self.move.length(): self.move = self.move.normalize()*speed
        self.change_position()
        if on_grass(self):
            self.life = min(self.life + self.config.rabbit_food_gain,
                            self.max_life)
        # mating attempt
        mated = 0
        if not on_rabbit_nest(self):
            for other in self.in_proximity_performance():
                if isinstance(other, Rabbit) and other.sex!=self.sex \
                   and self.pos.distance_to(other.pos)==0:
                    if self.shared.prng_move.random() < (1-self.life/self.max_life)**2:
                        self.reproduce(); mated = 1; self._decide()
                    break
        self._log(kill=0, mated=mated)
    # metrics
    def _log(self, *, kill:int, mated:int):
        self.save_data("kind",  "rabbit")
        self.save_data("sex",   self.sex)
        self.save_data("life_left", self.life)
        self.save_data("on_nest",   on_rabbit_nest(self))
        self.save_data("kill",  kill)
        self.save_data("mated", mated)

class Fox(Agent[PredPreyConfig]):
    fixed_sex  = None
    spawn_pool = []
    def on_spawn(self):
        r, c = random.choice(self.spawn_pool)
        self.pos = Vector2(c*CELL, r*CELL)
        self.sex = self.fixed_sex
        self.max_life = self.config.fox_lifespan
        self.life     = self.max_life
        self.move = Vector2(1,0).rotate(random.uniform(0,360))
    def _bounce(self):
        if inside_rabbit_nest_cell(self.pos) \
           or inside_rabbit_nest_cell(self.pos+self.move):
            self.move = self.move.rotate(180)
    def update(self):
        self.life -= 1
        if self.life <= 0:
            self._log(kill=0, mated=0)
            self.kill(); return
        self._bounce()
        if random.random() < 0.05:
            self.move = self.move.rotate(random.uniform(-45,45))
        speed = age_to_speed(self.config.v_min, self.config.v_max,
                             self.life, self.max_life)
        if self.move.length(): self.move = self.move.normalize()*speed
        self.change_position()
        kill = 0
        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit):
                other.kill(); kill = 1
                self.life = min(self.life + self.config.fox_food_gain,
                                self.max_life)
                break
        mated = 0
        for other in self.in_proximity_performance():
            if isinstance(other, Fox) and other.sex!=self.sex \
               and self.pos.distance_to(other.pos)==0:
                if self.shared.prng_move.random() < (1-self.life/self.max_life)**2:
                    self.reproduce(); mated = 1
                break
        self._log(kill=kill, mated=mated)
    def _log(self, *, kill:int, mated:int):
        self.save_data("kind",  "fox")
        self.save_data("sex",   self.sex)
        self.save_data("life_left", self.life)
        self.save_data("on_nest", False)
        self.save_data("kill",  kill)
        self.save_data("mated", mated)

# factories
def make_rabbit(sex, pool):
    class R(Rabbit): fixed_sex=sex; spawn_pool=pool
    return R
def make_fox(sex, pool):
    class F(Fox): fixed_sex=sex; spawn_pool=pool
    return F

# ────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    argp = argparse.ArgumentParser()
    argp.add_argument("--headless", action="store_true")
    args = argp.parse_args()

    cfg = PredPreyConfig(seed=13)
    cfg.window.width = cfg.window.height = CELL * GRID

    sim = HeadlessSimulation(cfg) if args.headless else Simulation(cfg)

    build(sim, "corridor")
    spawn_sites(sim)
    sim.batch_spawn_agents(20, make_rabbit("F", RABBIT_F_NESTS),
                           images=["images/rabbit.png"])
    sim.batch_spawn_agents(20, make_rabbit("M", RABBIT_M_NESTS),
                           images=["images/rabbit.png"])
    sim.batch_spawn_agents(20, make_fox("M", FOX_M_NESTS),
                           images=["images/fox.png"])
    sim.batch_spawn_agents(20, make_fox("F", FOX_F_NESTS),
                           images=["images/fox.png"])

    result = sim.run()
    df = result.snapshots

    base = Path(f"predprey_seed_{cfg.seed}")
    df.write_csv(base.with_suffix(".csv"))
    run_info = {
        "seed":            cfg.seed,
        "grass_patches":   len(grass_site_ids),
        "HOME_FACTOR":     HOME_FACTOR,
        "v_min":           cfg.v_min,
        "v_max":           cfg.v_max,
        "rabbit_lifespan": cfg.rabbit_lifespan,
        "duration_ticks":  cfg.duration,
    }
    with open(base.with_suffix(".json"), "w", encoding="utf-8") as fh:
        json.dump(run_info, fh, indent=2)
