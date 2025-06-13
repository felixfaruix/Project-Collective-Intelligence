import sys, os, math, random
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from pygame import Vector2
from vi import Agent, Config, Simulation
from vi.util import count
from enum import Enum, auto

random.seed(69)

@dataclass
class CockroachConfig(Config):
    alpha: float = 1.2
    beta: float = 0.4
    t_join: int = 60
    t_leave: int = 50
    t_settle: int = 150
    test_every: int = 60
    site_radius: float = 80
    site_radius_large: float = 80

class State(Enum):
    WANDERING = auto()
    JOINING = auto()
    STILL = auto()
    LEAVING = auto()

class Cockroach(Agent[CockroachConfig]):
    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self.simulation = simulation
        self.state = State.WANDERING
        self.timer = 0
        self.permanent = False
        self.preferred_site = None
        self._choose_random_direction()

    def _choose_random_direction(self, speed=1.5):
        angle = random.uniform(0, 360)
        self.move = Vector2(speed, 0).rotate(angle)

    def _count_neighbors(self):
        return sum(1 for _ in self.in_proximity_accuracy())

    def _inside_site(self):
        for site in self.simulation._sites:
            if self.pos.distance_to(site.rect.center) < self.config.site_radius:
                return True
        return False

    def which_site(self):
        for i, site in enumerate(self.simulation._sites):
            radius = self.config.site_radius
            if self.pos.distance_to(site.rect.center) < radius:
                return i
        return None

    def _p_join(self, n, site_index=None):
        base = 1 - math.exp(-self.config.alpha * n)
        if self.preferred_site is not None and site_index != self.preferred_site:
            return 0.2 * base  # discourage non-preferred site
        return base

    def _p_leave(self, n):
        return math.exp(-self.config.beta * n)

    def change_position(self):
        if self.permanent:
            return

        self.there_is_no_escape()
        self.timer += 1
        n = self._count_neighbors()
        inside = self._inside_site()
        site_index = self.which_site()

        if self.state == State.WANDERING:
            if site_index is not None and random.random() < self._p_join(n, site_index):
                self.state = State.JOINING
                self.timer = 0

        elif self.state == State.JOINING:
            if self.timer >= self.config.t_join:
                self.state = State.STILL
                self.move = Vector2(0, 0)
                self.timer = 0
                if self.preferred_site is None and site_index is not None:
                    self.preferred_site = site_index  # ← Remember first joined site

        elif self.state == State.STILL:
            if self.timer >= self.config.t_settle:
                self.permanent = True
                return
            if self.timer % self.config.test_every == 0:
                if random.random() < self._p_leave(n):
                    self.state = State.LEAVING
                    self._choose_random_direction(speed=3.0)
                    self.timer = 0

        elif self.state == State.LEAVING:
            if self.timer >= self.config.t_leave:
                self.state = State.WANDERING
                self._choose_random_direction()
                self.timer = 0

        if self.state != State.STILL:
            self.move = self.move.rotate(random.uniform(-10, 10))
            self.pos += self.move

class MySimulation(Simulation):
    def __init__(self, config):
        super().__init__(config)
        self.history_site0 = []
        self.history_site1 = []

    def after_update(self):
        super().after_update()
        site_counts = [0, 0]
        for agent in self._agents:
            if isinstance(agent, Cockroach):
                site_index = agent.which_site()
                if site_index is not None and site_index < 2:
                    site_counts[site_index] += 1
        self.history_site0.append(site_counts[0])
        self.history_site1.append(site_counts[1])

config = CockroachConfig(
    image_rotation=True,
    movement_speed=1,
    radius=50,
    fps_limit=120,
    seed=42,
    duration=60 * 90,
    site_radius=80,
    site_radius_large=80,
    alpha=1.2,
    beta=0.3,
    t_settle=150
)

x, y = config.window.as_tuple()

sim = (
    MySimulation(config)
    .spawn_site("images/site.png", x=275, y=375)
    .spawn_site("images/site.png", x=475, y=375)
    .batch_spawn_agents(100, Cockroach, images=["images/dot.png"])
)

sim.run()


shelter0 = sim.history_site0
shelter1 = sim.history_site1

ticks = np.arange(len(shelter0))
shelter0 = np.array(shelter0)
shelter1 = np.array(shelter1)

bordeaux = "#800020"
dark_beige = "#d2b48c"  # dark beige (tan/brown tone)

plt.figure(figsize=(10, 5))
plt.plot(shelter0, color=bordeaux, label='Shelter 1 (Bordeaux)', linewidth=2)
plt.plot(shelter1, color=dark_beige, label='Shelter 2 (Dark Beige)', linewidth=2)
plt.fill_between(ticks, shelter0, color=bordeaux, alpha=0.2)
plt.fill_between(ticks, shelter1, color=dark_beige, alpha=0.2)
plt.title("Shelter Aggregation Over Time", fontsize=14)
plt.xlabel("Time (ticks)")
plt.ylabel("Number of agents in shelter")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 5))
plt.stackplot(ticks, shelter0, shelter1,
              labels=["Shelter 1", "Shelter 2"],
              colors=[bordeaux, dark_beige], alpha=0.7)
plt.title("Stacked Shelter Occupancy", fontsize=14)
plt.xlabel("Time (ticks)")
plt.ylabel("Total Agents in Shelters")
plt.legend(loc='upper left')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

plt.figure(figsize=(6, 4))
final_counts = [shelter0[-1], shelter1[-1]]
plt.bar(["Shelter 1", "Shelter 2"], final_counts, color=[bordeaux, dark_beige])
plt.title("Final Shelter Occupancy")
plt.ylabel("Number of Agents")
plt.tight_layout()
plt.show()