# Pac-Man velocity (cells per second)
PAC_SPEED: float = 5.0

# Ghost velocity
GHOST_SPEED: float = 4.0

# Animation frame duration parameters
PAC_ANIM_SPEED: float = 10.0
PAC_ANIM_FRAMES: int = 3
PAC_DEATH_ANIM_SPEED: float = 6.0
PAC_DEATH_FRAMES: int = 8
PAC_RESPAWN_PAUSE: float = 1.0
SUPERPACGUM_ANIM_FPS: int = 12
SUPERPACGUM_ANIM_INTERVAL: float = 1.0
GHOST_ANIM_FPS: int = 12
# Input buffer tracking expiration window
PAC_INPUT_BUFFER: float = 0.4

# Inversion map to calculate sharp velocity direction switches
OPPOSITE_DIR: dict[str, str] = {
    'N': 'S',
    'S': 'N',
    'E': 'W',
    'W': 'E',
}

# Positional transformation deltas mapped by orientation index
DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    'N': (0, -1),
    'S': (0, 1),
    'E': (1, 0),
    'W': (-1, 0),
}

# Bitwise wall encoding lookup table matching cell layout flags
DIRECTION_BITS: dict[str, int] = {
    'N': 1,
    'E': 2,
    'S': 4,
    'W': 8,
}

# Sprite dimensions
SPRITE_SIZE: int = 48
# Cell dimensions
CELL_SIZE: int = 48
# HUD SIZE
HUD_HEIGHT: int = CELL_SIZE + 16
# Environment configuration constraints
FPS: int = 60
