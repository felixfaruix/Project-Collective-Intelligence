from dataclasses import dataclass
from pygame import Vector2
from vi import Agent, Config, Simulation
from vi.util import count
import random

random.seed(69)

@dataclass
class FlockingConfig(Config):
    # TODO: Modify the weights and observe the change in behaviour.
    alignment_weight: float = 2
    cohesion_weight: float = 1.5
    separation_weight: float = 2



class FlockingAgent(Agent[FlockingConfig]):
    # By overriding `change_position`, the default behaviour is overwritten.
    # Without making changes, the agents won't move.

    def __init__(self, images, simulation, pos = None, move = None):
        super().__init__(images, simulation, pos, move)
        angle = random.random() * 2 * 3.14159265
        self.move = Vector2(1, 0).rotate_rad(angle)

    def change_position(self):
        self.there_is_no_escape()

        neighbours_moves = []
        neighbours_pos = []
        
        for other, dist in self.in_proximity_accuracy():
            neighbours_moves.append(other.move)
            neighbours_pos.append(other.pos)


        # Alignment
        if not neighbours_moves:
            vn = Vector2(0,0)
        else:
            vn = (1/len(neighbours_moves)) * sum(neighbours_moves, Vector2(0,0))
        
        alignment = vn - self.move

        # Separation
        if not neighbours_moves:
            separation = Vector2(0,0)
        else:
            separation_sum = Vector2()
            for neighbor in neighbours_moves:
                separation_sum += (self.pos - neighbor)

            separation = (1/len(neighbours_moves)) * separation_sum

        # Cohesion
        if not neighbours_pos:
            xn = Vector2(0,0)
        else:
            xn = (1/len(neighbours_pos)) * sum(neighbours_pos, Vector2(0,0))

        cohesion_force = Vector2(xn) - self.pos
        
        cohesion = Vector2(cohesion_force) - self.move        



        f_total = (self.config.alignment_weight*alignment + self.config.separation_weight*separation + self.config.cohesion_weight*cohesion) / 1
        self.move += f_total
        max_velocity = self.config.movement_speed
        if self.move.length() > max_velocity and self.move.length() != 0:
            self.move = self.move.normalize() * max_velocity
        
        self.pos += self.move

        if any(self.obstacle_intersections()):
            self.move = -(self.move+Vector2(10,10))

            if self.move.length() > max_velocity and self.move.length() != 0:
                self.move = self.move.normalize() * max_velocity

            self.pos += self.move
        
        


config = Config()
x, y = config.window.as_tuple()

(
    Simulation(
        # TODO: Modify `movement_speed` and `radius` and observe the change in behaviour.
        FlockingConfig(image_rotation=True, movement_speed=5, radius=50, fps_limit=60, seed=69, duration=100*60)
    )
    .batch_spawn_agents(100, FlockingAgent, images=["images/triangle.png"])
    .spawn_obstacle("images/triangle@200px.png", x // 2, y // 2)
    .run()
)
