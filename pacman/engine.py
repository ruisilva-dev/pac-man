from mazegenerator import MazeGenerator
from pacman.config import Configuration
from pacman.items import Consumable, Pacgum, SuperPacgum

# Pac-Man velocity (cells per second)
PAC_SPEED: float = 5.0

# Animation frame duration parameters
PAC_ANIM_SPEED: float = 10.0
PAC_ANIM_FRAMES: int = 3

# Inversion map to calculate sharp velocity direction switches
OPPOSITE_DIR: dict[str, str] = {
    'N': 'S',
    'S': 'N',
    'E': 'W',
    'W': 'E',
}

# Input buffer tracking expiration window
PAC_INPUT_BUFFER: float = 0.4

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
    'S': 4,
    'E': 2,
    'W': 8,
}


class PacmanEngine:
    """The core logic engine handling game mechanics and state records.

    This class provides a clean data interface contract that coordinates
    the grid matrix layout, running metrics, and player attributes
    independently of any active front-end graphical visualization loops.

    Attributes:
        config: The configuration state instance reference mapping bounds.
        score: Aggregated game points earned by the player instance.
        lives: Remainder tracking tally for player survival attempts.
        grid: Two-dimensional matrix representing active map cell encodings.
        grid_rows: Total integer row count of the active simulation space.
        grid_cols: Total integer column count of the active simulation space.
        pac_col: Active discrete X-axis block coordinate of the player.
        pac_row: Active discrete Y-axis block coordinate of the player.
        pac_dir: Active cardinal character direction of player movement.
        pac_next_dir: Buffered target direction requested by user hardware.
        pac_next_dir_timer: Tracked lifecycle age of the current
            buffered input.
        pac_move_progress: Interpolation progress float bounded between
            0.0 and 1.0.
        pac_anim_index: Current visual frame animation index offset.
        pac_anim_timer: Elapsed delta accumulator scaling game
            animation frames.
        items: Two-dimensional layout matrix tracking active collectibles.
    """

    def __init__(self, config: Configuration) -> None:
        """Initializes a new game logic session with safe initial states.

        Args:
            config: Fully loaded game initialization options container.
        """
        self.config: Configuration = config
        self.score: int = 0
        self.lives: int = config.lives

        generator: MazeGenerator = MazeGenerator(
            size=(15, 15),
            perfect=False,
            seed=config.seed
        )

        self.grid: list[list[int]] = generator.maze
        self.grid_rows: int = len(self.grid)
        self.grid_cols: int = (
            len(self.grid[0]) if self.grid_rows > 0 else 0
        )

        # Establish starting coordinate slots within central safe pathways
        posy: int = (self.grid_rows - 5) // 2
        posx: int = (self.grid_cols - 7) // 2
        self.pac_col: int = posx + 3
        self.pac_row: int = posy + 2

        self.pac_dir: str = 'E'
        self.pac_next_dir: str = self.pac_dir
        self.pac_next_dir_timer: float = 0.0
        self.pac_move_progress: float = 0.0
        self.pac_anim_index: int = 0
        self.pac_anim_timer: float = 0.0

        # Initialize the item layout matrix to track active collectibles
        self.items: list[list[Consumable | None]] = [
            [
                Pacgum(self.config.points_per_pacgum) if val < 15 else None
                for val in row
            ]
            for row in self.grid
        ]
        self.items[self.pac_row][self.pac_col] = None

        # Maze corner mapping: (start_row, start_col, r_step, c_step)
        corners_config: list[tuple[int, int, int, int]] = [
            (0, 0, 1, 1),
            (0, self.grid_cols - 1, 1, -1),
            (self.grid_rows - 1, 0, -1, 1),
            (self.grid_rows - 1, self.grid_cols - 1, -1, -1)
        ]

        for s_row, s_col, r_step, c_step in corners_config:
            r, c = s_row, s_col
            while (
                0 <= r < self.grid_rows
                and 0 <= c < self.grid_cols
                and self.grid[r][c] == 15
            ):
                r += r_step
                c += c_step

            if 0 <= r < self.grid_rows and 0 <= c < self.grid_cols:
                self.items[r][c] = SuperPacgum(
                    self.config.points_per_super_pacgum
                )

    def _can_move(self, col: int, row: int, direction: str) -> bool:
        """Verifies if path progression can occur from a matrix point.

        Args:
            col: Target column index array identifier.
            row: Target row index array identifier.
            direction: Character key representing candidate direction.

        Returns:
            True if movement is unblocked; False if a wall exists.
        """
        bit: int = DIRECTION_BITS[direction]
        return not (self.grid[row][col] & bit)

    def _update_pacman(self, dt: float) -> None:
        """Updates player mechanics, coordinate values, and vector timers.

        Args:
            dt: Delta time tracking in seconds since last frame pass.
        """
        # Expire tracking values within the input queue buffer
        if self.pac_next_dir != self.pac_dir:
            self.pac_next_dir_timer += dt
            if self.pac_next_dir_timer >= PAC_INPUT_BUFFER:
                self.pac_next_dir = self.pac_dir
                self.pac_next_dir_timer = 0.0
        else:
            self.pac_next_dir_timer = 0.0

        # Progress visual animation cycles
        self.pac_anim_timer += dt * PAC_ANIM_SPEED
        if self.pac_anim_timer >= 1.0:
            self.pac_anim_timer -= 1.0
            self.pac_anim_index = (
                (self.pac_anim_index + 1) % PAC_ANIM_FRAMES
            )

        # Attempt application of keyboard directional inputs
        if self._can_move(
            self.pac_col, self.pac_row, self.pac_next_dir
        ):
            is_opposite: bool = (
                self.pac_next_dir == OPPOSITE_DIR[self.pac_dir]
            )
            is_committed: bool = self.pac_move_progress > 0.0

            if is_opposite and is_committed:
                # Handle mid-cell rapid direction reversal changes cleanly
                self.pac_dir = self.pac_next_dir
                self.pac_move_progress = 1.0 - self.pac_move_progress
                dc, dr = DIRECTION_DELTAS[OPPOSITE_DIR[self.pac_dir]]
                self.pac_col += dc
                self.pac_row += dr
            elif not is_committed:
                # Only accept new directions when landing flush on cells
                self.pac_dir = self.pac_next_dir

        # Halt sequence instantly if a wall stops forward progression
        if not self._can_move(self.pac_col, self.pac_row, self.pac_dir):
            self.pac_move_progress = 0.0
            return

        # Advance mechanical cell travel interpolation counters
        self.pac_move_progress += dt * PAC_SPEED
        if self.pac_move_progress >= 1.0:
            self.pac_move_progress = 0.0

            # Transfer data records cleanly to the next destination cell
            dc, dr = DIRECTION_DELTAS[self.pac_dir]
            self.pac_col += dc
            self.pac_row += dr

            # Pull the pacgum, increase score, delete reference
            item = self.items[self.pac_row][self.pac_col]
            if item is not None:
                item.on_consume(self)
                self.items[self.pac_row][self.pac_col] = None

    def update(self, dt: float) -> None:
        """Advances active simulation mechanics processing loops.

        Args:
            dt: Delta time tracking in seconds since last frame pass.
        """
        self._update_pacman(dt)
