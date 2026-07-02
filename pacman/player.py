from typing import TYPE_CHECKING
from pacman.constants import (
    PAC_SPEED, OPPOSITE_DIR, PAC_INPUT_BUFFER, DIRECTION_DELTAS
)

if TYPE_CHECKING:
    from pacman.engine import PacmanEngine


class Player:
    """Encapsulates Pac-Man's positional state, input buffer, and movement.

    Attributes:
        home_col: Origin spawn X-axis coordinate.
        home_row: Origin spawn Y-axis coordinate.
        col: Active discrete X-axis grid block coordinate.
        row: Active discrete Y-axis grid block coordinate.
        current_dir: Active cardinal direction of player movement.
        next_dir: Buffered target direction requested by user input.
        next_dir_timer: Tracked expiration lifecycle age of the buffered input.
        move_progress: Cell travel progress float between 0.0 and 1.0.
        is_dying: Status flag signaling the player is in a death sequence.
    """

    def __init__(self, home_col: int, home_row: int) -> None:
        """Initializes a player entity at its default home pathway coordinates.

        Args:
            home_col: Origin spawn column index block mapping central pathways.
            home_row: Origin spawn row index block mapping central pathways.
        """
        self.home_col: int = home_col
        self.home_row: int = home_row
        self.col: int = home_col
        self.row: int = home_row

        self.current_dir: str = 'E'
        self.next_dir: str = 'E'
        self.next_dir_timer: float = 0.0
        self.move_progress: float = 0.0
        self.is_dying: bool = False

    def reset_position(self) -> None:
        """Resets logical movement parameters back to home spawn defaults."""
        self.is_dying = False
        self.col = self.home_col
        self.row = self.home_row
        self.current_dir = 'E'
        self.next_dir = self.current_dir
        self.next_dir_timer = 0.0
        self.move_progress = 0.0

    def buffer_input(self, direction: str) -> None:
        """Enqueues a pending orientation command and flushes its decay timer.

        Args:
            direction: Character code representing the requested direction.
        """
        self.next_dir = direction
        self.next_dir_timer = 0.0

    def update(self, dt: float, engine: "PacmanEngine") -> None:
        """Advances input lifetimes, cell step movements, and point collection.

        Args:
            dt: Delta time tracking in seconds since the last frame.
            engine: Shared reference to central engine.
        """
        # Expire tracking values within the input queue buffer
        if self.next_dir != self.current_dir:
            self.next_dir_timer += dt
            if self.next_dir_timer >= PAC_INPUT_BUFFER:
                self.next_dir = self.current_dir
                self.next_dir_timer = 0.0
        else:
            self.next_dir_timer = 0.0

        # Attempt application of keyboard directional inputs
        if engine.can_move(
            self.col, self.row, self.next_dir
        ):
            is_opposite: bool = (
                self.next_dir == OPPOSITE_DIR[self.current_dir]
            )
            is_committed: bool = self.move_progress > 0.0

            if is_opposite and is_committed:
                # Handle mid-cell rapid direction reversal changes cleanly
                self.current_dir = self.next_dir
                self.move_progress = 1.0 - self.move_progress
                dc, dr = DIRECTION_DELTAS[OPPOSITE_DIR[self.current_dir]]
                self.col += dc
                self.row += dr
            elif not is_committed:
                # Only accept new directions when landing flush on cells
                self.current_dir = self.next_dir

        # Halt sequence instantly if a wall stops forward progression
        if not engine.can_move(self.col, self.row, self.current_dir):
            self.move_progress = 0.0
            return

        # Advance mechanical cell travel interpolation counters
        speed_factor = 2.0 if engine.cheat_speed else 1.0
        self.move_progress += dt * PAC_SPEED * speed_factor
        dc, dr = DIRECTION_DELTAS[self.current_dir]
        if self.move_progress >= 0.8:
            item_col, item_row = self.col + dc, self.row + dr
            # Pull the pacgum, increase score, delete reference
            item = engine.items[item_row][item_col]
            if item is not None:
                item.on_consume(engine)
                engine.items[item_row][item_col] = None

        if self.move_progress >= 1.0:
            self.move_progress -= 1.0

            # Transfer data records cleanly to the next destination cell
            self.col += dc
            self.row += dr
