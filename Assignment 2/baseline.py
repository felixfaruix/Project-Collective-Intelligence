import cProfile
from multiprocessing import Pool
from pygame import Vector2
from vi import Agent, HeadlessSimulation, Simulation
from dataclasses import dataclass
from vi.config import Config, dataclass
from pygame import Vector2
from map_design import obstacle_size, grid, build, is_walkable_at, print_walkable_grid

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

def attempt_move(agent, speed):
    future_pos = agent.pos + agent.move
    if is_walkable_at(future_pos):
        agent.pos = future_pos
        return
    for _ in range(5):
        angle = random.uniform(0, 360)
        trial_move = Vector2(1, 0).rotate(angle).normalize() * speed
        if is_walkable_at(agent.pos + trial_move):
            agent.move = trial_move
            agent.pos += trial_move
            return
    agent.move = Vector2()

class Rabbit(Agent[PredPreyConfig]):
    def on_spawn(self, speed=1):
        self._my_id = id(self)
        self.max_lifespan = self.config.rabbit_lifespan
        self.lifespan = self.max_lifespan
        self.sex = random.choice(["M", "F"])
        self.image_index = getattr(self, "image_index", -1)


        # Assign to sex-based nest
        if self.sex == "M":
            tile_x, tile_y = random.choice(nest_top_left)
        else:
            tile_x, tile_y = random.choice(nest_top_right)

        self.pos = Vector2(tile_x * obstacle_size, tile_y * obstacle_size)
        self.nest_pos = self.pos
        self.returning_to_nest = False
        self._still_stuck = False
        angle = random.uniform(0, 360)
        self.move = Vector2(speed, 0).rotate(angle)


    def update(self):
        self.save_data("frame", self.shared.counter)

        self.save_data("id", self._my_id)

        self.save_data("Kind", "Rabbit")
        self.save_data("Sex", getattr(self, "sex", "?"))
        self.save_data("Lifespan", getattr(self, "lifespan", -1))
        self.save_data("x", self.pos.x)
        self.save_data("y", self.pos.y)
        self.save_data("image_index", getattr(self, "image_index", -1))




        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return
        
        urgency = 1 - (self.lifespan / self.max_lifespan)
        speed = self.config.v_min + urgency * (self.config.v_max - self.config.v_min)

        if self.returning_to_nest:
            to_nest = self.nest_pos - self.pos
            if to_nest.length() < 3:
                self.returning_to_nest = False
            else:
                self.move = (0.7 * to_nest.normalize() + 0.3 * self.move).normalize()

        elif self.shared.prng_move.random() < 0.01 + (1 - urgency) * 0.05:
            angle = random.uniform(0, 360)
            self.move = Vector2(1, 0).rotate(angle)

        if self.move.length() == 0:
           self.move = Vector2(1, 0).rotate(random.uniform(0, 360))

        self.move = self.move.normalize() * speed
        attempt_move(self, speed)

        for other in self.in_proximity_performance():
            if isinstance(other, Rabbit) and other.sex != self.sex:
                if self.pos.distance_to(other.pos) == 0:
                    urgency = 1 - (self.lifespan / self.max_lifespan)
                    prob = urgency ** 2
                    if self.shared.prng_move.random() < prob:
                        self.reproduce()
                        self.returning_to_nest = True
                        break


class Fox(Agent[PredPreyConfig]):
    def on_spawn(self):
        self._my_id = id(self)
        self.max_lifespan = self.config.fox_lifespan
        self.lifespan = self.max_lifespan
        self.sex = random.choice(["M", "F"])
        self.image_index = getattr(self, "image_index", -1)


        tile_x, tile_y = random.choice(nest_bottom_left if self.sex == "M" else nest_bottom_right)
        self.pos = Vector2(tile_x * obstacle_size, tile_y * obstacle_size)

        angle = random.uniform(0, 360)
        self.move = Vector2(1, 0).rotate(angle)
        self._still_stuck = False

    def update(self):

        self.save_data("frame", self.shared.counter)

        self.save_data("id", self._my_id)

        self.save_data("Kind", "Fox")
        self.save_data("Sex", getattr(self, "sex", "?"))
        self.save_data("Lifespan", getattr(self, "lifespan", -1))
        self.save_data("x", self.pos.x)
        self.save_data("y", self.pos.y)
        self.save_data("image_index", getattr(self, "image_index", -1))



        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            return

        speed = self.config.v_min + (1 - (self.lifespan / self.max_lifespan)) * (self.config.v_max - self.config.v_min)
        if self.move.length() > 0:
            self.move = self.move.normalize() * speed

        attempt_move(self, speed)

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
    build(sim, "structured")
    print_walkable_grid()
    sim.batch_spawn_agents(70, Rabbit, images=["images/rabbit.png"])
    sim.batch_spawn_agents(50, Fox, images=["images/fox.png"])
    sim.run()
