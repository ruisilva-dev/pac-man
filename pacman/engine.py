from mazegenerator import MazeGenerator
from pacman.player import Player
from pacman.config import Configuration
from pacman.items import Pacgum, SuperPacgum
from pacman.ghosts import Ghost, Blinky, Pinky, Clyde, Inky
from pacman.constants import (
    COLLISION_DISTANCE,
    PAC_START_PAUSE,
    PAC_RESPAWN_PAUSE,
    DIRECTION_DELTAS,
    DIRECTION_BITS,
    EXTRA_LIFE_SCORE
)


class PacmanEngine:
    """The core logic engine handling game mechanics and state records.

    This class provides a clean data interface contract that coordinates
    the grid matrix layout, running metrics, and player attributes
    independently of any active front-end graphical visualization loops.

    Attributes:
        config: The configuration state instance reference mapping bounds.
        level: The current progression level index.
        level_timer: The remaining countdown time for the active level.
        score: Aggregated game points earned by the player instance.
        lives: Remainder tracking tally for player survival attempts.
        respawn_pause_timer: Countdown delay after a death before restarting.
        cheat_invincible: Flag granting immunity to ghost collisions.
        cheat_freeze: Flag stopping level timer and ghost entity movement.
        cheat_speed: Flag doubling the player's movement velocity.
        ghost_speed: Dynamically scaled movement velocity for enemies.
        grid: Two-dimensional matrix representing active map cell encodings.
        grid_rows: Total integer row count of the active simulation space.
        grid_cols: Total integer column count of the active simulation space.
        player: Isolated tracking entity instance modeling Pac-Man properties.
        items: Two-dimensional layout matrix tracking active collectibles.
        ghosts: Active list of autonomous ghost entities.
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
        # Cheats
        self.cheat_invincible: bool = False
        self.cheat_freeze: bool = False
        self.cheat_speed: bool = False
        # Arcade milestones
        self.bonus_life_awarded: bool = False

        self._build_level(seed=config.seed)

    def _get_level_metrics(self) -> tuple[float, tuple[int, int], float]:
        """Retrieves ghost speed, grid size, and timer based on level stage.

        Returns:
            A tuple containing the ghost speed (float), target grid dimensions
            (tuple of width and height ints), and the level time limit (float).
        """
        level_speeds: dict[int, float] = {
            1: 3.6, 2: 3.6, 3: 3.8, 4: 3.8, 5: 4.0,
            6: 4.0, 7: 4.2, 8: 4.2, 9: 4.5, 10: 4.5
        }
        level_sizes: dict[int, tuple[int, int]] = {
            1: (15, 15), 2: (15, 15), 3: (15, 15), 4: (15, 15), 5: (17, 17),
            6: (17, 17), 7: (17, 17), 8: (17, 17), 9: (19, 19), 10: (19, 19)
        }
        level_timers: dict[int, float] = {
            1: 105.0, 2: 105.0, 3: 105.0, 4: 105.0, 5: 145.0,
            6: 145.0, 7: 145.0, 8: 145.0, 9: 180.0, 10: 180.0
        }

        return (
            level_speeds.get(self.level, 4.5),
            level_sizes.get(self.level, (19, 19)),
            level_timers.get(self.level, 180.0)
        )

    def _spawn_items(self) -> None:
        """Populates the maze corridors with pacgums and super pacgums."""
        self.items = [
            [
                Pacgum(self.config.points_per_pacgum)
                if val in (3, 5, 6, 7, 9, 10, 11, 12, 13, 14) else None
                for _, val in enumerate(row)
            ]
            for _, row in enumerate(self.grid)
        ]
        self.items[self.player.row][self.player.col] = None

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

    def _spawn_ghosts(self) -> None:
        """Initializes the four ghosts into their respective map corners."""
        max_c = self.grid_cols - 1
        max_r = self.grid_rows - 1

        self.ghosts: list[Ghost] = [
            Blinky(0, 0, 0, 0, self.get_start_dir(0, 0)),
            Pinky(max_c, 0, max_c, 0, self.get_start_dir(max_c, 0)),
            Clyde(0, max_r, 0, max_r, self.get_start_dir(0, max_r)),
            Inky(max_c, max_r, max_c, max_r, self.get_start_dir(max_c, max_r))
        ]

    def _build_level(self, seed: int = 0) -> None:
        """Generates the maze matrix and populates all entities and items.

        Args:
            seed: Optional integer to dictate deterministic map layouts.
        """
        self.ghost_speed, target_size, self.level_timer = (
            self._get_level_metrics()
        )

        generator: MazeGenerator = MazeGenerator(
            size=target_size, perfect=False, seed=seed
        )

        self.grid: list[list[int]] = generator.maze
        self.grid_rows: int = len(self.grid)
        self.grid_cols: int = len(self.grid[0]) if self.grid_rows > 0 else 0

        # Establish starting coordinate slots within central safe pathways
        pos_y: int = (self.grid_rows - 5) // 2
        pos_x: int = (self.grid_cols - 7) // 2

        self.player: Player = Player(pos_x + 3, pos_y + 2)

        self._spawn_items()
        self._spawn_ghosts()

    def _check_collisions(self) -> None:
        """Checks ghost collisions, triggering death or ghost consumption.

        Uses the continuous (interpolated) positions of Pac-Man and each
        ghost rather than raw grid indices, so a collision only fires
        when the two are visually overlapping. Each actor's position is
        its cell plus its movement progress along its current direction.
        """
        pdc, pdr = DIRECTION_DELTAS[self.player.current_dir]
        pac_x: float = self.player.col + pdc * self.player.move_progress
        pac_y: float = self.player.row + pdr * self.player.move_progress

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
                if self.cheat_invincible:
                    continue

                # If caught by ghost marks pacman as dying
                self.player.is_dying = True
                return

            elif ghost.state == "FRIGHTENED":
                self.score += self.config.points_per_ghost
                ghost.state = "EATEN"
                # Set timer and respawn home
                ghost.state_timer = 5.0

    def get_path_distance(
        self,
        start_c: int,
        start_r: int,
        target_c: int,
        target_r: int,
    ) -> float:
        """Evaluates shortest legal path distance using a BFS.

        Args:
            start_c: Column index of the starting evaluation coordinate.
            start_r: Row index of the starting evaluation coordinate.
            target_c: Column index of the destination target node.
            target_r: Row index of the destination target node.

        Returns:
            The total path distance step count, or float("inf") if blocked.
        """
        if start_c == target_c and start_r == target_r:
            return 0.0

        queue: list[tuple[int, int, float]] = [(start_c, start_r, 0.0)]
        visited: set[tuple[int, int]] = {(start_c, start_r)}

        while queue:
            curr_c, curr_r, dist = queue.pop(0)
            for direction in DIRECTION_DELTAS:
                if self.can_move(curr_c, curr_r, direction):
                    dc, dr = DIRECTION_DELTAS[direction]

                    next_c = curr_c + dc
                    next_r = curr_r + dr

                    if next_c == target_c and next_r == target_r:
                        return dist + 1.0
                    elif (next_c, next_r) not in visited:
                        visited.add((next_c, next_r))
                        queue.append((next_c, next_r, dist + 1.0))

        return float("inf")

    def has_items(self) -> bool:
        """Checks if any consumable pacgums remain in the maze.

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
        self.player.reset_position()

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
        if self.player.is_dying:
            return
        if self.respawn_pause_timer > 0.0:
            self.respawn_pause_timer -= dt
            return

        if not self.cheat_freeze:
            self.level_timer -= dt

        if self.level_timer <= 0.0:
            self.lives -= 1
            self.player.is_dying = False
            self.player.reset_position()
            for ghost in self.ghosts:
                ghost.reset()
            self.respawn_pause_timer = PAC_RESPAWN_PAUSE
            self.level_timer = self._get_level_metrics()[2]
            return

        self.player.update(dt, self)

        # Tick all ghost routing lookahead cycles forward
        if not self.cheat_freeze:
            for ghost in self.ghosts:
                ghost.update(dt, self)

        # Check if a grid collision boundary has been tripped
        self._check_collisions()

        # Add extra life at score milestone
        if self.score >= EXTRA_LIFE_SCORE and not self.bonus_life_awarded:
            self.lives = min(5, self.lives + 1)
            self.bonus_life_awarded = True

    def activate_frightened_mode(self) -> None:
        """Flips all active ghost states to vulnerable mode."""
        for ghost in self.ghosts:
            if ghost.state != "EATEN":
                ghost.state = "FRIGHTENED"
                ghost.state_timer = 10.0

    def advance_level(self) -> None:
        """Regenerates the maze layout for subsequent randomized levels."""
        self.level += 1
        self._build_level()

    def restart(self) -> None:
        """Resets the engine to a fresh game at level 1."""
        self.level = 1
        self.score = 0
        self.lives = self.config.lives
        self.level_timer = 90.0
        self.bonus_life_awarded = False
        self._build_level(seed=self.config.seed)
        self.respawn_pause_timer = PAC_START_PAUSE
