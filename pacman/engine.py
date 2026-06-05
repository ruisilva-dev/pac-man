from mazegenerator import MazeGenerator
from pacman.config import Configuration
from pacman.items import Consumable, Pacgum, SuperPacgum
from pacman.ghosts import Ghost
from pacman.constants import (
    PAC_SPEED,
    COLLISION_DISTANCE,
    OPPOSITE_DIR,
    PAC_INPUT_BUFFER,
    PAC_RESPAWN_PAUSE,
    DIRECTION_DELTAS,
    DIRECTION_BITS,
)


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
        items: Two-dimensional layout matrix tracking active collectibles.
    """

    def __init__(self, config: Configuration) -> None:
        """Initializes a new game logic session with safe initial states.

        Args:
            config: Fully loaded game initialization options container.
        """
        self.config: Configuration = config
        self.level: int = 1
        self.level_timer: float = 90.0
        self.score: int = 0
        self.lives: int = config.lives
        # Pause before re-spawning
        self.respawn_pause_timer: float = 0.0

        self._build_level(seed=config.seed)

    def _build_level(self, seed: int = 0) -> None:
        """Generates the maze matrix and populates all entities and items.

        Args:
            seed: Optional integer to dictate deterministic map layouts.
        """
        generator: MazeGenerator = MazeGenerator(
            size=(15, 15),
            perfect=False,
            seed=seed
        )

        self.grid: list[list[int]] = generator.maze
        self.grid_rows: int = len(self.grid)
        self.grid_cols: int = (
            len(self.grid[0]) if self.grid_rows > 0 else 0
        )

        # Establish starting coordinate slots within central safe pathways
        posy: int = (self.grid_rows - 5) // 2
        posx: int = (self.grid_cols - 7) // 2
        self.pac_home_col: int = posx + 3
        self.pac_home_row: int = posy + 2

        self.pac_col: int = self.pac_home_col
        self.pac_row: int = self.pac_home_row

        self.pac_dir: str = 'E'
        self.pac_next_dir: str = self.pac_dir
        self.pac_next_dir_timer: float = 0.0
        self.pac_move_progress: float = 0.0
        # Establishes if pacman is dead or alive
        self.pac_dying: bool = False
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

        max_c = self.grid_cols - 1
        max_r = self.grid_rows - 1

        self.ghosts: list[Ghost] = [
            Ghost(0, 0, 0, 0, 0, self.get_start_dir(0, 0)),
            Ghost(max_c, 0, max_c, 0, 1, self.get_start_dir(max_c, 0)),
            Ghost(0, max_r, 0, max_r, 2, self.get_start_dir(0, max_r)),
            Ghost(
                max_c,
                max_r,
                max_c,
                max_r,
                3,
                self.get_start_dir(max_c, max_r)
            )
        ]

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

        # Attempt application of keyboard directional inputs
        if self.can_move(
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
        if not self.can_move(self.pac_col, self.pac_row, self.pac_dir):
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

    def _check_collisions(self) -> None:
        """Checks ghost collisions, triggering death or ghost consumption.

        Uses the continuous (interpolated) positions of Pac-Man and each
        ghost rather than raw grid indices, so a collision only fires
        when the two are visually overlapping. Each actor's position is
        its cell plus its movement progress along its current direction.
        """
        pdc, pdr = DIRECTION_DELTAS[self.pac_dir]
        pac_x: float = self.pac_col + pdc * self.pac_move_progress
        pac_y: float = self.pac_row + pdr * self.pac_move_progress

        for ghost in self.ghosts:
            gdc, gdr = DIRECTION_DELTAS[ghost.current_dir]
            ghost_x: float = ghost.col + gdc * ghost.move_progress
            ghost_y: float = ghost.row + gdr * ghost.move_progress

            # Distance in cell units between the two interpolated points.
            dist: float = (
                (pac_x - ghost_x) ** 2 + (pac_y - ghost_y) ** 2
            ) ** 0.5
            if dist >= COLLISION_DISTANCE:
                continue

            if ghost.state == "CHASE":
                # If caught by ghost marks pacman as dieing
                self.pac_dying = True
                return

            elif ghost.state == "FRIGHTENED":
                self.score += self.config.points_per_ghost
                ghost.state = "EATEN"
                # Set timer and respawn home
                ghost.state_timer = 5.0

    def has_items(self) -> bool:
        """Checks if any consumable pellets remain in the maze.

        Returns:
            True if at least one item is left; False if the maze is clear.
        """
        return any(
            any(item is not None for item in row)
            for row in self.items
        )

    def get_start_dir(self, col: int, row: int) -> str:
        """Dynamically detects open map corridor from a starting matrix cell.

        Args:
            col: Starting X-axis grid coordinate.
            row: Starting Y-axis grid coordinate.

        Returns:
            A valid cardinal direction character ('N', 'S', 'E', 'W').
        """
        for direction in ['E', 'W', 'S', 'N']:
            if self.can_move(col, row, direction):
                return direction
        return 'N'  # Fallback

    def finish_death(self) -> None:
        """Resets Pacman to its respawn point and decrements 1 life"""
        # Reset pac-man state
        self.lives -= 1
        self.pac_dying = False
        self.pac_col = self.pac_home_col
        self.pac_row = self.pac_home_row
        self.pac_dir = 'E'
        self.pac_next_dir = self.pac_dir
        self.pac_next_dir_timer = 0.0
        self.pac_move_progress = 0.0

        for ghost in self.ghosts:
            ghost.reset()

        self.respawn_pause_timer = PAC_RESPAWN_PAUSE

    def can_move(self, col: int, row: int, direction: str) -> bool:
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

    def update(self, dt: float) -> None:
        """Advances active simulation mechanics processing loops.

        Args:
            dt: Delta time tracking in seconds since last frame pass.
        """
        if self.pac_dying:
            return
        if self.respawn_pause_timer > 0.0:
            self.respawn_pause_timer -= dt
            return

        self.level_timer -= dt
        if self.level_timer <= 0.0:
            self.lives -= 1
            self.level_timer = 90.0

            current_seed = self.config.seed if self.level == 1 else 0
            self._build_level(seed=current_seed)

            self.respawn_pause_timer = PAC_RESPAWN_PAUSE
            return

        self._update_pacman(dt)

        # Tick all ghost routing lookahead cycles forward
        for ghost in self.ghosts:
            ghost.update(dt, self)

        # Check if a grid collision boundary has been tripped
        self._check_collisions()

    def activate_frightened_mode(self) -> None:
        """Flips all active ghost states to vulnerable mode."""
        for ghost in self.ghosts:
            if ghost.state != "EATEN":
                ghost.state = "FRIGHTENED"
                ghost.state_timer = 10.0

    def advance_level(self) -> None:
        """Regenerates the maze layout for subsequent randomized levels."""
        self.level += 1
        self.level_timer = 90.0
        self._build_level()
