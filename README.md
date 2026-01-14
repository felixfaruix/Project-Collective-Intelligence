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
