from dataclasses import dataclass
import enum
import math
import random

from pygame import Vector2
from pygame.surface import Surface
from vi import Agent, Config, HeadlessSimulation, Simulation

@dataclass
class CockroachConfig(Config):
    # sensing & sites
    site_radius: float = 50          # must match the .spawn_site() image
    # stochastic PFSM parameters             
    alpha: float = 0.5               # higher alpha: agents join sites more readily
    beta:  float = 0.5             # lower beta: agents less likely to leave, but still possible
    # deterministic timers  (ticks)          ────────────────
    t_join_max:  int = 60             # join state is shorter for quicker aggregation
    t_leave_max: int = 200            # leave state is a bit shorter
    test_every:  int = 30           # check for leaving more frequently
    # motion
    wandering_speed: float = 2.5
    leaving_speed:   float = 5.0     # a bit faster to really exit the site

class State(enum.IntEnum):
    WANDERING = 0
    JOINING   = 1
    STILL     = 2
    LEAVING   = 3

class Cockroach(Agent[CockroachConfig]):
    
    def __init__(self, images: list[Surface], simulation: HeadlessSimulation[CockroachConfig], pos: Vector2 | None = None, move: Vector2 | None = None) -> None:
        super().__init__(images, simulation, pos, move)
        
    def on_spawn(self) -> None:
        # one-off initialization happens here
        angle = random.uniform(0, 360)
        self.move = Vector2(self.config.wandering_speed, 0).rotate(angle)
        self.state  = State.WANDERING
        self.timer  = 0
            
# ---------- utility functions -------------------------
            
    def _count_neighbours(self) -> int:
        """Returns number of agents within radius."""
        return sum(
            1 for _ in list(self.in_proximity_accuracy())
        )
    
    def _closest_site_vec(self) -> Vector2 | None:
            """
            Smallest vector that points from the agent to the centre of the
            nearest aggregation site.  Returns None when no sites exist.
            """
            nearest, best_dist = None, float("inf")

            # every site created with spawn_site() is stored here
            # TODO get all spawn sites from simulation
            site = Vector2(375,375)        # type: ignore # ➊
            d = self.pos.distance_to(site)      # site.pos is a Vector2
            if d < best_dist:
                nearest, best_dist = site, d

            return (nearest - self.pos) if nearest else None
    
    def _inside_site(self) -> bool:
        v = self._closest_site_vec()
        return v is not None and v.length() < self.config.site_radius
    
    # ---------- probability functions  (lecture slide) ---------------
    
    def _p_join(self, n: int) -> float:
        return 1 - math.exp(-self.config.alpha * n)          

    def _p_leave(self, n: int) -> float:
        return math.exp(-self.config.beta * n)               
    
    # ---------- move agent ------------------------

    def change_position(self):
        self.there_is_no_escape()     # keep agents inside the window
        n = self._count_neighbours()
        inside = self._inside_site()
        self.timer += 1

        # wandering
        if self.state == State.WANDERING:
            # random walk
            if random.random() < 0.02:                     # small steering noise
                self.move = self.move.rotate(random.uniform(-90, 90))
            # probabilistic transition
            if inside and random.random() < self._p_join(n):
                self.state, self.timer = State.JOINING, 0

        # join
        elif self.state == State.JOINING:
            # move towards site centre
            to_c = self._closest_site_vec()
            if to_c:                                       # steer gently
                self.move = to_c.normalize() * self.config.wandering_speed
            if self.timer >= self.config.t_join_max:
                self.state, self.timer = State.STILL, 0
                self.move = Vector2()                      # full stop

        # stay
        elif self.state == State.STILL:
            # immobile – test Pleave every D ticks
            if self.timer % self.config.test_every == 0:
                if random.random() < self._p_leave(n):
                    self.state, self.timer = State.LEAVING, 0
                    # pick a random direction to exit quickly
                    angle = random.uniform(0, 360)
                    self.move = Vector2(self.config.leaving_speed, 0).rotate(angle)

        # leave
        elif self.state == State.LEAVING:
            # keep moving in chosen direction
            if self.timer >= self.config.t_leave_max:
                self.state, self.timer = State.WANDERING, 0
                # slow back to wandering speed
                self.move.scale_to_length(self.config.wandering_speed)

        # finally, execute the motion chosen above
        self.pos += self.move
        
        
sim_cfg = CockroachConfig(
    image_rotation=True,
    movement_speed=1,   
    radius=50,
    fps_limit=60,
    seed=69,
)

x, y = sim_cfg.window.as_tuple()

(
    Simulation(sim_cfg)                     
    .spawn_site("/images/site.png", x=375, y=375)
    .batch_spawn_agents(50, Cockroach, images=["/images/dot.png"])
    .run()
)