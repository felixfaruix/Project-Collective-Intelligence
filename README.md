# Collective Intelligence: Exploration vs Exploitation

Agent-based simulation studying how spatially segregated agents with limited lifespans balance exploration and exploitation for survival and reproduction.

## Research Question

How do internal states (lifespan, energy) influence agents' willingness to leave safe territory in search of food or mates, and how do these decisions affect survival and reproduction?

## Model

- **Agents**: Foxes (predators) and rabbits (prey), each with male/female variants
- **Environment**: Grid world with four corner nests connected by corridors
- **Mechanics**:
  - Lifespan decreases each tick; death occurs at zero
  - Movement speed increases as lifespan depletes (urgency-driven exploration)
  - Foxes hunt rabbits to regain lifespan
  - Sexual reproduction requires opposite-sex contact; probability scales with urgency
  - Nests are predator-free safe zones but contain no food

## Key Dynamics

Agents face a trade-off: staying in nests is safe but leads to starvation and no reproduction. Leaving exposes them to predation but enables feeding and mating. Urgency emerges naturally — as lifespan drops, agents move faster and mate more readily.

## Formulas (Custom)

**Speed as a function of remaining lifespan**

As agents approach death, movement speed increases quadratically:

$$v(t) = v_{min} + \left(1 - \frac{L_{remaining}}{L_{max}}\right)^2 \cdot (v_{max} - v_{min})$$

**Lifespan recovery on feeding**

When a fox eats a rabbit, it regains lifespan (capped at maximum):

$$L_{new} = \min(L_{current} + \Delta L_{food}, L_{max})$$

**Urgency function**

A unified urgency score combining internal state and local opportunity:

$$U = \alpha \cdot \left(1 - \frac{L_{remaining}}{L_{max}}\right) + \beta \cdot (1 - O_{local})$$

Where $O_{local}$ represents nearby opportunities (prey or mates). Urgency scales movement:

$$v = v_{min} + U \cdot (v_{max} - v_{min})$$

**Reproduction probability**

Probability of mating upon contact scales with urgency (desperation-driven reproduction):

$$P_{reproduce} \propto \left(1 - \frac{L_{remaining}}{L_{max}}\right)^2$$

## Repository Structure

```
├── vi/                      # Simulation framework ("Violet")
│   ├── agent.py             # Base Agent class (extend this for custom behavior)
│   ├── simulation.py        # Simulation engine (headless + GUI modes)
│   ├── config.py            # Configuration dataclasses
│   ├── proximity.py         # Spatial chunking for neighbor detection
│   └── metrics.py           # Data collection utilities
│
├── Assignment 0/            # Flocking (Boids)
│   └── flocking.py          # Reynolds flocking with alignment/cohesion/separation
│
├── Assignment 1/            # Aggregation
│   └── aggregation.py       # Agent clustering behavior
│
├── Assignment 2/            # Predator-Prey (main project)
│   ├── baseline.py          # Fox-rabbit simulation entry point
│   ├── map_design.py        # Grid layout with nests and corridors
│   └── images/              # Agent and environment sprites
│
├── images/                  # Shared sprite assets
├── main.py                  # Alternative entry point
└── snapshots_*.csv          # Collected simulation data
```

## Running

```bash
# With GUI
python Assignment\ 2/baseline.py

# Headless (batch experiments)
python Assignment\ 2/baseline.py --headless
```

## Dependencies

- Python 3.10+
- pygame
- polars
- vi (included simulation framework)
