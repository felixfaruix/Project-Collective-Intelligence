import sys, os , math, random
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) #to import vi module

from dataclasses import dataclass
from pygame import Vector2
from vi import Agent, Config, Simulation
from vi.util import count
from enum import Enum, auto


random.seed(69)

@dataclass
class CockroachConfig(Config):
    alpha: float = 0.7        #Pjoin
    beta: float = 0.4          #Pleave 
    t_join: int = 60           #JOINING → STILL time
    t_leave: int = 50          #LEAVING → WANDERING time
    test_every: int = 30       
    site_radius: float = 50    # radius of aggregation site
    site_radius_large: float = 90  #stage2 

class State(Enum):
    WANDERING = auto()
    JOINING = auto()
    STILL = auto()
    LEAVING = auto()

#Cockroach agent class
class Cockroach(Agent[CockroachConfig]):
    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self.simulation = simulation
        self.state = State.WANDERING
        self.timer = 0
        self._choose_random_direction()

    #random movement direction 
    def _choose_random_direction(self, speed=1.5):
        angle = random.uniform(0, 360)
        self.move = Vector2(speed, 0).rotate(angle)

    #count neighboring agents in range
    def _count_neighbors(self):
        return sum(1 for _ in self.in_proximity_accuracy())
    
    #check if agent is inside any site
    def _inside_site(self):
        for site in self.simulation._sites:
            if self.pos.distance_to(site.rect.center) < self.config.site_radius:
                return True
        return False
    
    def which_site(self): #Returns the site index (0 or 1) if inside a site, else None
        for i, site in enumerate(self.simulation._sites):
            radius = (
            self.config.site_radius if i == 0 else self.config.site_radius_large
            )
            if self.pos.distance_to(site.rect.center) < radius:
               return i
        return None

    #def is_in_site(self):  
        #return self._inside_site()

    #probability to joint site based on local density
    def _p_join(self, n):
        return 1 - math.exp(-self.config.alpha * n)

    #probability to leave the site based on local density
    def _p_leave(self, n):
        return math.exp(-self.config.beta * n)
  
    
    def change_position(self):
        self.there_is_no_escape() #stay within bounds
        self.timer += 1
        n = self._count_neighbors()
        inside = self._inside_site()

        if self.state == State.WANDERING:
            if inside and random.random() < self._p_join(n):
                self.state = State.JOINING
                self.timer = 0

        elif self.state == State.JOINING:
            if self.timer >= self.config.t_join:
                self.state = State.STILL
                self.move = Vector2(0, 0)
                self.timer = 0

        elif self.state == State.STILL:
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
            self.pos += self.move

class MySimulation(Simulation):
    def __init__(self, config):
        super().__init__(config)
        #self.history = []  #when we have one shelter-stage1
        self.history_site0 = []  #small shelter
        self.history_site1 = []  #bigger one

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



        #---stage1--
        #count_in_site = sum(
           # 1 for agent in self._agents
            #if isinstance(agent, Cockroach) and agent.which_site() is not None
        #)
        #self.history.append(count_in_site)
        #----------


config = CockroachConfig(
    image_rotation=True,
    movement_speed=1,
    radius=50,
    fps_limit=60,
    #seed=69,
    seed=42,   #this is for exp1 stage2 after the first run
    duration=60 * 60,
    site_radius = 50,
    site_radius_large=90
)

x, y = config.window.as_tuple()

#one shelter and 100 agents
#sim = (
    #MySimulation(config)
    #.spawn_site("images/site.png", x=375, y=375)
    #.batch_spawn_agents(100, Cockroach, images=["images/dot.png"])
#)
#Two shelters, different sizes
sim = (
    MySimulation(config)
    .spawn_site("images/site.png", x=275, y=375)         
    .spawn_site("images/site_large.png", x=475, y=375)     
    .batch_spawn_agents(100, Cockroach, images=["images/dot.png"])
)

sim.run()

#plt.plot(sim.history)
#plt.xlabel("Time (tick)")
#plt.ylabel("Number of agents in shelter")
#plt.title("Aggregation over time")
#plt.grid(True)
#plt.show()


plt.plot(sim.history_site0, label="Shelter 1 (smaller)")
plt.plot(sim.history_site1, label="Shelter 2 (bigger)")
plt.xlabel("Time (tick)")
plt.ylabel("Number of agents in shelter")
plt.title("Aggregation comparison: small vs. large shelter")
plt.legend()
plt.grid(True)
plt.show()