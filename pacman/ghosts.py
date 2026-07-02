from typing import TYPE_CHECKING
from pacman.constants import DIRECTION_DELTAS, OPPOSITE_DIR

if TYPE_CHECKING:
    from pacman.engine import PacmanEngine


class Ghost:
    """Represents an autonomous enemy entity driven by AI targeting profiles.

    Ghosts navigate the map grid independently using specialized pathfinding
    strategies dictated by their unique identities. They shift dynamically
    across operational phases while utilizing lookahead vectors.

    Attributes:
        col: Active discrete X-axis block coordinate inside the maze.
        row: Active discrete Y-axis block coordinate inside the maze.
        home_col: X-axis spawn and respawn anchor block coordinate.
        home_row: Y-axis spawn and respawn anchor block coordinate.
        move_progress: Interpolation progress tracking bounded between
            0.0 and 1.0.
        start_dir: Cardinal heading assigned at session initialization.
        current_dir: Active cardinal movement heading index.
        target_col: Calculated destination X-axis coordinate cell.
        target_row: Calculated destination Y-axis coordinate cell.
        state: Behavior mode tracking descriptor ("CHASE", "FRIGHTENED",
            "EATEN").
        previous_state: State tracking latch for mid-tile reversal triggers.
        state_timer: Remaining active lifecycle countdown for transient
            states.
        eaten_speed: Dynamic velocity utilized during base return journeys.
    """

    def __init__(
        self,
        col: int,
        row: int,
        home_col: int,
        home_row: int,
        start_dir: str = "N"
    ) -> None:
        """Initializes a ghost instance with routing boundaries.

        Args:
            col: Starting X-axis grid layout coordinate slot.
            row: Starting Y-axis grid layout coordinate slot.
            home_col: Default target home anchor X-axis tile.
            home_row: Default target home anchor Y-axis tile.
            start_dir: Initial cardinal heading character selection.
        """
        self.col: int = col
        self.row: int = row
        self.home_col: int = home_col
        self.home_row: int = home_row
        self.move_progress: float = 0.0
        self.start_dir: str = start_dir
        self.current_dir: str = start_dir
        self.target_col: int = home_col
        self.target_row: int = home_row
        self.state: str = "CHASE"
        self.previous_state: str = "CHASE"
        self.state_timer: float = 0.0
        self.eaten_speed: float = 0.0

    def get_chase_target(self, engine: "PacmanEngine") -> tuple[int, int]:
        """Calculates the specific chase destination tile for this ghost type.

        Args:
            engine: Shared reference to the central core logic driver.

        Returns:
            A tuple containing the target (column, row) indices.
        """
        return self.home_col, self.home_row  # Default fallback

    def reset(self) -> None:
        """Resets the ghost entity to initial spawn parameters."""
        self.col = self.home_col
        self.row = self.home_row
        self.move_progress = 0.0
        self.current_dir = self.start_dir
        self.target_col = self.home_col
        self.target_row = self.home_row
        self.state = "CHASE"
        self.previous_state = "CHASE"
        self.state_timer = 0.0

    def update(self, dt: float, engine: "PacmanEngine") -> None:
        """Advances entity AI tracking logic and cell travel transitions.

        Args:
            dt: Delta time parameter in seconds elapsed since last frame.
            engine: Shared reference to the central core logic driver.
        """
        # Advance state lifecycle timers
        if self.state in ["FRIGHTENED", "EATEN"]:
            self.state_timer -= dt

        # Handle Frightened expiration
        if self.state == "FRIGHTENED" and self.state_timer <= 0.0:
            self.state = "CHASE"

        # Handle state transition
        if self.state != self.previous_state:
            if self.move_progress > 0.0:
                self.move_progress = 1.0 - self.move_progress
                dc, dr = DIRECTION_DELTAS[self.current_dir]
                self.col = max(0, min(self.col + dc, engine.grid_cols - 1))
                self.row = max(0, min(self.row + dr, engine.grid_rows - 1))
            self.current_dir = OPPOSITE_DIR[self.current_dir]
            self.previous_state = self.state

        # Target coordinate recalculation
        if self.state == "CHASE":
            self.target_col, self.target_row = self.get_chase_target(engine)

        elif self.state == "FRIGHTENED":
            # Target furthest corner away from pac-man
            max_c: int = engine.grid_cols - 1
            max_r: int = engine.grid_rows - 1
            corners: list[tuple[int, int]] = [
                (0, 0), (max_c, 0), (0, max_r), (max_c, max_r)
            ]

            max_dist: float = -1.0
            flee_target: tuple[int, int] = (self.home_col, self.home_row)
            for c, r in corners:
                dist: float = float(
                    (c - engine.player.col) ** 2 + (r - engine.player.row) ** 2
                )
                if dist > max_dist:
                    max_dist = dist
                    flee_target = (c, r)

            self.target_col, self.target_row = flee_target

        elif self.state == "EATEN":
            # Target home corner
            self.target_col = self.home_col
            self.target_row = self.home_row

            if self.state_timer <= 0.0:
                self.reset()
                return

        # Calculate dynamic speed
        if self.state == "EATEN":
            dist_left = engine.get_path_distance(
                self.col, self.row, self.home_col, self.home_row
            )
            if dist_left == float("inf"):
                dist_col = abs(self.col - self.home_col)
                dist_row = abs(self.row - self.home_row)
                dist_left = float(dist_col + dist_row)

            time_left = max(0.1, self.state_timer - 0.2)
            active_speed = dist_left / time_left
        else:
            active_speed = engine.ghost_speed

        self.move_progress += dt * active_speed

        # Arrived on new cell
        while self.move_progress >= 1.0:
            self.move_progress -= 1.0

            dc, dr = DIRECTION_DELTAS[self.current_dir]
            self.col = max(0, min(self.col + dc, engine.grid_cols - 1))
            self.row = max(0, min(self.row + dr, engine.grid_rows - 1))

            # Valid moves from current position
            valid_moves: list[str] = []
            for direction in DIRECTION_DELTAS:
                dc_next, dr_next = DIRECTION_DELTAS[direction]
                next_c = self.col + dc_next
                next_r = self.row + dr_next

                # Prevent negative wrapping and check boundaries strictly
                if (
                    0 <= next_c < engine.grid_cols
                    and 0 <= next_r < engine.grid_rows
                ):
                    if (
                        engine.can_move(self.col, self.row, direction) and
                        direction != OPPOSITE_DIR[self.current_dir]
                    ):
                        valid_moves.append(direction)

            if not valid_moves:
                valid_moves.append(OPPOSITE_DIR[self.current_dir])

            # Find best option to get closer to target
            best_choice: str = ""
            min_distance: float = float("inf")

            # Current distance to pac-man
            curr_to_pac: int = (
                (self.col - engine.player.col) ** 2 +
                (self.row - engine.player.row) ** 2
            )

            for direction in valid_moves:
                dc, dr = DIRECTION_DELTAS[direction]

                next_col = self.col + dc
                next_row = self.row + dr

                dist = engine.get_path_distance(
                    next_col,
                    next_row,
                    self.target_col,
                    self.target_row,
                )

                # Fall back to Euclidean distance if ghost is walled off
                if dist == float("inf"):
                    col_dist = (next_col - self.target_col) ** 2
                    row_dist = (next_row - self.target_row) ** 2

                    # No square root to avoid unnecessary computation
                    dist = float(col_dist + row_dist)

                if self.state == "FRIGHTENED":
                    # Distance to pac-man from next position
                    next_to_pac = (
                        (next_col - engine.player.col) ** 2 +
                        (next_row - engine.player.row) ** 2
                    )

                    # Apply heavy penalty for approaching pac-man
                    if next_to_pac < curr_to_pac:
                        dist += 100.0

                if dist < min_distance:
                    min_distance = dist
                    best_choice = direction

            if best_choice:
                self.current_dir = best_choice


class Blinky(Ghost):
    """The Red Ghost: Aggressively chases Pac-Man's exact tile coordinates."""

    def get_chase_target(self, engine: "PacmanEngine") -> tuple[int, int]:
        """Calculates the target tile by matching the player's position.

        Args:
            engine: Shared reference to the central game logic driver.

        Returns:
            A tuple containing the target (column, row) grid indices.
        """
        return (engine.player.col, engine.player.row)


class Pinky(Ghost):
    """The Pink Ghost: Ambushes 4 tiles ahead of Pac-Man's trajectory."""

    def get_chase_target(self, engine: "PacmanEngine") -> tuple[int, int]:
        """Calculates the target tile by projecting ahead of the player.

        Args:
            engine: Shared reference to the central game logic driver.

        Returns:
            A tuple containing the target (column, row) grid indices.
        """
        dc, dr = DIRECTION_DELTAS[engine.player.current_dir]
        raw_c: int = engine.player.col + (dc * 4)
        raw_r: int = engine.player.row + (dr * 4)

        # Clamp inside maze boundaries safely
        target_col: int = max(0, min(raw_c, engine.grid_cols - 1))
        target_row: int = max(0, min(raw_r, engine.grid_rows - 1))

        return (target_col, target_row)


class Clyde(Ghost):
    """The Orange Ghost: Flees to its corner if too close to Pac-Man."""

    def get_chase_target(self, engine: "PacmanEngine") -> tuple[int, int]:
        """Calculates the target tile based on proximity to the player.

        Args:
            engine: Shared reference to the central game logic driver.

        Returns:
            A tuple containing the target (column, row) grid indices.
        """
        dx: int = engine.player.col - self.col
        dy: int = engine.player.row - self.row
        distance_squared: int = (dx * dx) + (dy * dy)

        # Chase if outside an 8-tile radius, otherwise retreat to home corner
        if distance_squared > 64:
            target_col: int = engine.player.col
            target_row: int = engine.player.row
        else:
            target_col = self.home_col
            target_row = self.home_row

        return (target_col, target_row)


class Inky(Ghost):
    """The Blue Ghost: Mirrors a position offset from Blinky's coordinates."""

    def get_chase_target(self, engine: "PacmanEngine") -> tuple[int, int]:
        """Calculates the target tile using Blinky as a mirrored pivot point.

        Args:
            engine: Shared reference to the central game logic driver.

        Returns:
            A tuple containing the target (column, row) grid indices.
        """
        # Blinky is guaranteed to be the first ghost spawned in the engine list
        blinky: Ghost = engine.ghosts[0]

        # Calculate offset vector from Blinky to Pac-Man, and extend it
        raw_c: int = engine.player.col + (engine.player.col - blinky.col)
        raw_r: int = engine.player.row + (engine.player.row - blinky.row)

        # Clamp inside maze boundaries safely
        target_col: int = max(0, min(raw_c, engine.grid_cols - 1))
        target_row: int = max(0, min(raw_r, engine.grid_rows - 1))

        return (target_col, target_row)
