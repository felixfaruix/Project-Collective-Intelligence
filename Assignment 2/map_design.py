from vi import Simulation

OB = 24
obstacle_image = "images/obstacle.png"

GRID = 30


def wall(sim: Simulation, r: int, c: int) -> None:
    sim.spawn_obstacle(obstacle_image, c * OB, r * OB)


NEST = 8
HUB  = 12
CORR = 3

# convenient indices
tl = 1                       # nests start at row/col 1
br = GRID - NEST - 1         # bottom/right nest top-left = 21 (for 30×30)
hub_r0 = (GRID - HUB) // 2   # 9
hub_r1 = hub_r0 + HUB - 1    # 20
hub_c0 = hub_r0              # centred square
hub_c1 = hub_r1

# corridor spans
top_rows    = range(hub_r0 - CORR, hub_r0)          # 6-8
bottom_rows = range(hub_r1 + 1, hub_r1 + 1 + CORR)  # 21-23
left_cols   = range(hub_c0 - CORR, hub_c0)          # 6-8
right_cols  = range(hub_c1 + 1, hub_c1 + 1 + CORR)  # 21-23

# ───────────────── map builders ────────────────
def hub_map(sim: Simulation):
    """Build the 4-nests-plus-hub map."""
    for r in range(GRID):
        for c in range(GRID):

            # 8×8 nests
            in_tl = tl <= r < tl + NEST and tl <= c < tl + NEST
            in_tr = tl <= r < tl + NEST and br <= c < br + NEST
            in_bl = br <= r < br + NEST and tl <= c < tl + NEST
            in_br = br <= r < br + NEST and br <= c < br + NEST

            # 12×12 hub
            in_hub = hub_r0 <= r <= hub_r1 and hub_c0 <= c <= hub_c1

            # 3-tile corridors
            in_top    = r in top_rows    and hub_c0 <= c <= hub_c1
            in_bottom = r in bottom_rows and hub_c0 <= c <= hub_c1
            in_left   = c in left_cols   and hub_r0 <= r <= hub_r1
            in_right  = c in right_cols  and hub_r0 <= r <= hub_r1

            walkable = in_tl or in_tr or in_bl or in_br or \
                       in_hub or in_top or in_bottom or in_left or in_right

            if not walkable:
                wall(sim, r, c)

# ───────────────── spawn lists (inner 6×6 cores) ─────────────────
core_rng_tl = range(tl + 1, tl + 1 + 6)         # 2-7
core_rng_br = range(br + 1, br + 1 + 6)         # 22-27

nest_top_left     = [(r, c) for r in core_rng_tl for c in core_rng_tl]
nest_top_right    = [(r, c) for r in core_rng_tl for c in core_rng_br]
nest_bottom_left  = [(r, c) for r in core_rng_br for c in core_rng_tl]
nest_bottom_right = [(r, c) for r in core_rng_br for c in core_rng_br]

all_nests = (nest_top_left + nest_top_right +
             nest_bottom_left + nest_bottom_right)

# ───────────────── external API ─────────────────
def build(sim: Simulation, name: str):
    if name != "corridor":
        raise ValueError("Only 'corridor' is implemented in this simple map")
    hub_map(sim)
