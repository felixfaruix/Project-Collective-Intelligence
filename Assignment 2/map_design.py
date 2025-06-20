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

def is_walkable(r: int, c: int) -> bool:
    """Check if a cell is walkable (same logic as before)."""
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

    return in_tl or in_tr or in_bl or in_br or \
           in_hub or in_top or in_bottom or in_left or in_right

def has_walkable_neighbor(r: int, c: int) -> bool:
    """Check if a cell has at least one walkable neighbor."""
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID and 0 <= nc < GRID and is_walkable(nr, nc):
                return True
    return False

def is_necessary_perimeter(r: int, c: int) -> bool:
    """Check if perimeter obstacle is necessary (exclude middle 10 blocks on each side)."""
    # Corner areas and sides excluding middle 10 blocks
    if r == 0 or r == GRID - 1:  # Top or bottom edge
        return c < 10 or c >= 20  # Keep corners, remove middle 10 (columns 10-19)
    elif c == 0 or c == GRID - 1:  # Left or right edge
        return r < 10 or r >= 20  # Keep corners, remove middle 10 (rows 10-19)
    return False

def add_inner_walls(sim: Simulation):
    """Add the U-shaped and C-shaped barriers and the central square."""
    
    # Top corridor U-shape (open to top, mirrored)
    for c in range(13, 17): wall(sim, 7, c)
    wall(sim, 6, 13)
    wall(sim, 6, 16)
    
    # Bottom corridor U-shape (open to bottom, mirrored)
    for c in range(13, 17): wall(sim, 22, c)
    wall(sim, 23, 13)
    wall(sim, 23, 16)
    # Left corridor C-shape (open to left, mirrored)
    for r in range(13, 17): wall(sim, r, 7)
    wall(sim, 13, 6)
    wall(sim, 16, 6)
    
    # Right corridor C-shape (open to right, mirrored)
    for r in range(13, 17): wall(sim, r, 22)
    wall(sim, 13, 23)
    wall(sim, 16, 23)
    
"""     # Central 4x4 square
    r_start, c_start = 13, 13
    r_end, c_end = 16, 16
    for c in range(c_start, c_end + 1):
        wall(sim, r_start, c)  # Top
        wall(sim, r_end, c)    # Bottom
    for r in range(r_start + 1, r_end):
        wall(sim, r, c_start)  # Left
        wall(sim, r, c_end)    # Right """

def hub_map(sim: Simulation):
    """Build the 4-nests-plus-hub map with optimized obstacles."""
    for r in range(GRID):
        for c in range(GRID):
            is_necessary_perimeter_cell = is_necessary_perimeter(r, c)
            is_boundary = not is_walkable(r, c) and has_walkable_neighbor(r, c)
            
            if is_necessary_perimeter_cell or is_boundary:
                wall(sim, r, c)
    
    # Add the extra walls from the new design
    add_inner_walls(sim)

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
