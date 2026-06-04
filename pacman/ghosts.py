from typing import TYPE_CHECKING
from pacman.constants import DIRECTION_DELTAS, GHOST_SPEED, OPPOSITE_DIR
import random

if TYPE_CHECKING:
    from pacman.engine import PacmanEngine


class Ghost:
    def __init__(
        self,
        col: int,
        row: int,
        home_col: int,
        home_row: int,
        ghost_id: int,
        start_dir: str = "N"
    ) -> None:
        self.col: int = col
        self.row: int = row
        self.home_col: int = home_col
        self.home_row: int = home_row
        self.ghost_id: int = ghost_id
        self.move_progress: float = 0.0
        self.start_dir: str = start_dir
        self.current_dir: str = start_dir
        self.target_col: int = home_col
        self.target_row: int = home_row
        self.state: str = "CHASE"
        self.state_timer: float = 0.0
        self.eaten_speed: float = 0.0

    def _bfs_distance(
        self,
        start_c: int,
        start_r: int,
        target_c: int,
        target_r: int,
        engine: "PacmanEngine"
    ) -> float:
        if start_c == target_c and start_r == target_r:
            return 0.0

        queue: list[tuple[int, int, float]] = [(start_c, start_r, 0.0)]
        visited: set[tuple[int, int]] = {(start_c, start_r)}

        while queue:
            curr_c, curr_r, dist = queue.pop(0)
            for direction in DIRECTION_DELTAS:
                if engine.can_move(curr_c, curr_r, direction):
                    dc, dr = DIRECTION_DELTAS[direction]

                    next_c = curr_c + dc
                    next_r = curr_r + dr

                    if next_c == target_c and next_r == target_r:
                        return dist + 1.0
                    elif (next_c, next_r) not in visited:
                        visited.add((next_c, next_r))
                        queue.append((next_c, next_r, dist + 1.0))

        return float("inf")

    def reset(self) -> None:
        """Resets the ghost to its initial spawn state."""
        self.col = self.home_col
        self.row = self.home_row
        self.move_progress = 0.0
        self.current_dir = self.start_dir
        self.target_col = self.home_col
        self.target_row = self.home_row
        self.state = "CHASE"
        self.state_timer = 0.0

    def update(self, dt: float, engine: "PacmanEngine") -> None:
        # Advance state lifecycle timers
        if self.state in ["FRIGHTENED", "EATEN"]:
            self.state_timer -= dt

        # Handle Frightened expiration
        if self.state == "FRIGHTENED" and self.state_timer <= 0.0:
            self.state = "CHASE"

        # Target coordinate recalculation
        if self.state == "CHASE":
            if self.ghost_id == 0:
                # Blinky: Chase directly
                self.target_col = engine.pac_col
                self.target_row = engine.pac_row

            elif self.ghost_id == 1:
                # Pinky: Ambush 4 tiles ahead of Pac-Man's trajectory vector
                dc, dr = DIRECTION_DELTAS[engine.pac_dir]
                raw_c = engine.pac_col + (dc * 4)
                raw_r = engine.pac_row + (dr * 4)

                # Clamp inside maze boundaries
                self.target_col = max(0, min(raw_c, engine.grid_cols - 1))
                self.target_row = max(0, min(raw_r, engine.grid_rows - 1))

            elif self.ghost_id == 2:
                # Clyde: Flee back to corner if within 8-tile radius threshold
                dx = engine.pac_col - self.col
                dy = engine.pac_row - self.row
                distance_squared = (dx * dx) + (dy * dy)

                if distance_squared > 64:  # 8 tiles squared = 64
                    self.target_col = engine.pac_col
                    self.target_row = engine.pac_row
                else:
                    self.target_col = self.home_col
                    self.target_row = self.home_row

            elif self.ghost_id == 3:
                # Inky: Mirror offset tactic
                # Target Pac-Man's position flipped over Blinky's coordinates
                blinky = engine.ghosts[0]
                raw_c = engine.pac_col + (engine.pac_col - blinky.col)
                raw_r = engine.pac_row + (engine.pac_row - blinky.row)

                # Clamp inside maze boundaries
                self.target_col = max(0, min(raw_c, engine.grid_cols - 1))
                self.target_row = max(0, min(raw_r, engine.grid_rows - 1))

        # Handle Eaten routing and speed
        if self.state == "EATEN":
            self.target_col = self.home_col
            self.target_row = self.home_row

            if self.state_timer <= 0.0:
                self.col = self.home_col
                self.row = self.home_row
                self.move_progress = 0.0
                self.state = "CHASE"
                return

            dist_left = self._bfs_distance(
                self.col, self.row, self.home_col, self.home_row, engine
            )
            if dist_left == float("inf"):
                dist_col = abs(self.col - self.home_col)
                dist_row = abs(self.row - self.home_row)
                dist_left = float(dist_col + dist_row)

            time_left = max(0.1, self.state_timer - 0.2)
            active_speed = dist_left / time_left
        else:
            active_speed = GHOST_SPEED

        self.move_progress += dt * active_speed

        # Arrived on new cell
        if self.move_progress >= 1.0:
            self.move_progress -= 1.0

            dc, dr = DIRECTION_DELTAS[self.current_dir]
            self.col += dc
            self.row += dr

            # Valid moves from current position
            valid_moves: list[str] = []
            for direction in DIRECTION_DELTAS:
                dc_next, dr_next = DIRECTION_DELTAS[direction]
                next_c = self.col + dc_next
                next_r = self.row + dr_next

                # Prevent negative wrapping and check map boundaries strictly
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
            best_choice = ""

            if self.state == "FRIGHTENED":
                best_choice = random.choice(valid_moves)

            else:
                min_distance = float("inf")
                for direction in valid_moves:
                    dc, dr = DIRECTION_DELTAS[direction]

                    next_col = self.col + dc
                    next_row = self.row + dr

                    dist = self._bfs_distance(
                        next_col,
                        next_row,
                        self.target_col,
                        self.target_row,
                        engine
                    )

                    # Fall back to Euclidean distance if ghost is walled off
                    if dist == float("inf"):
                        col_dist = (next_col - self.target_col) ** 2
                        row_dist = (next_row - self.target_row) ** 2

                        # No square root, because if A**2 < B**2, then A < B
                        # Avoids unnecessary computation
                        dist = float(col_dist + row_dist)

                    if dist < min_distance:
                        min_distance = dist
                        best_choice = direction

            if best_choice:
                self.current_dir = best_choice
