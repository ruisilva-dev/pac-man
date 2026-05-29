import pygame
from pacman.engine import PacmanEngine, DIRECTION_DELTAS

# Sprite dimensions
SPRITE_SIZE: int = 48
# Cell dimensions
CELL_SIZE: int = 48

# Bitmask
BIT_N: int = 1
BIT_E: int = 2
BIT_S: int = 4
BIT_W: int = 8

# Environment configuration constraints
FPS: int = 60


class GameRenderer:
    """Manages graphical rendering operations using Pygame surfaces.

    Attributes:
        engine: Shared logic configuration state source container.
        grid: Nested integer sequence modeling active layout bitmasks.
        rows: Total row count of the grid.
        cols: Total column count of the grid.
        width: Window width in pixels.
        height: Window height in pixels.
        screen: Render target surface.
        pac_sprites: Categorized collection matching direction keys to
            textures.
        maze_sprites: Tileset collection mapping bitmask values to
            surfaces.
    """

    def __init__(self, engine: PacmanEngine) -> None:
        """Initializes window and loads graphical assets.

        Args:
            engine: Shared logic core engine reference.
        """
        self.engine: PacmanEngine = engine
        self.grid: list[list[int]] = self.engine.grid
        self.current_theme: str = "classic"
        self.rows: int = len(self.grid)
        self.cols: int = len(self.grid[0]) if self.rows > 0 else 0
        self.width: int = self.cols * CELL_SIZE
        self.height: int = self.rows * CELL_SIZE
        self.screen: pygame.Surface = (
            pygame.display.set_mode((self.width, self.height))
        )
        pygame.display.set_caption("Pac-Man")

        self.pac_sprites: dict[str, list[pygame.Surface]] = {}
        self.floor_sprite: pygame.Surface
        self.maze_sprites: dict[
            str, dict[int, pygame.Surface]
        ] = {}
        self._load_sprites()
        self.background_surface: pygame.Surface = (
            pygame.Surface((self.width, self.height))
        )
        self._render_background()

    def cell_pos(self, col: int, row: int) -> tuple[int, int]:
        """Calculates top-left screen pixel position for a grid cell.

        Args:
            col: Grid column index.
            row: Grid row index.

        Returns:
            A tuple of (x, y) pixel coordinates.
        """
        return (col * CELL_SIZE, row * CELL_SIZE)

    def cell_center(self, x: int, y: int) -> tuple[int, int]:
        """Calculates center pixel position from a cell origin.

        Args:
            x: Top-left x pixel coordinate.
            y: Top-left y pixel coordinate.

        Returns:
            A tuple of centered (x, y) pixel coordinates.
        """
        return (x + CELL_SIZE // 2, y + CELL_SIZE // 2)

    def _closed_bitmask(
        self, row_idx: int, col_idx: int
    ) -> int:
        """Calculates the effective bitmask for a closed cell (value 15).

        Args:
            row_idx: Row index of the closed cell.
            col_idx: Column index of the closed cell.

        Returns:
            Effective bitmask value between 0 and 14.
        """
        effective: int = 15
        if row_idx > 0 and self.grid[row_idx - 1][col_idx] == 15:
            effective &= ~BIT_N
        if (col_idx < self.cols - 1
                and self.grid[row_idx][col_idx + 1] == 15):
            effective &= ~BIT_E
        if (row_idx < self.rows - 1
                and self.grid[row_idx + 1][col_idx] == 15):
            effective &= ~BIT_S
        if col_idx > 0 and self.grid[row_idx][col_idx - 1] == 15:
            effective &= ~BIT_W
        return effective

    def _render_background(self) -> None:
        """Pre-Renders the maze using tileset sprites."""
        floor: pygame.Surface = self.floor_sprite
        wall_frames: dict[int, pygame.Surface] = self.maze_sprites['walls']
        closed_frames: dict[int, pygame.Surface] = (
            self.maze_sprites['closed']
        )

        for row_idx, row in enumerate(self.grid):
            for col_idx, cell_value in enumerate(row):
                x, y = self.cell_pos(col_idx, row_idx)

                # 1. Floor in all the cells
                self.background_surface.blit(floor, (x, y))

                # 2. Normal Wall or Closed Cell
                if cell_value == 15:
                    closed = self._closed_bitmask(
                        row_idx, col_idx
                    )
                    if closed in closed_frames:
                        self.background_surface.blit(closed_frames[closed],
                                                     (x, y))
                elif cell_value in wall_frames:
                    self.background_surface.blit(wall_frames[cell_value],
                                                 (x, y))

    def draw_grid(self) -> None:
        """Renders the pre-calculated background surface to the screen."""
        self.screen.blit(self.background_surface, (0, 0))

    def _load_sprites(self) -> None:
        """Dispatches asset loading across all sprite categories."""
        self._load_pacman_sprites()
        self._load_maze_sprites()

    def _load_maze_sprites(self) -> None:
        """Loads floor tile and slices wall and closed sprite sheets."""
        basepath: str = (
            f"pacman/render/themes/{self.current_theme}/maze"
        )

        # 1. Floor sprite.
        floor = pygame.image.load(f"{basepath}/floor.png").convert()
        self.floor_sprite = (
            pygame.transform.scale(floor, (CELL_SIZE, CELL_SIZE))
        )

        # 2. Sheet to normal cells (bitmask 0 to 14)
        sheet: pygame.Surface = (
            pygame.image.load(f"{basepath}/walls_sheet.png").convert_alpha()
        )
        wall_frames: dict[int, pygame.Surface] = {}
        for i in range(15):
            crop = sheet.subsurface(
                pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
            )
            wall_frames[i] = (
                pygame.transform.scale(crop, (CELL_SIZE, CELL_SIZE))
            )
        self.maze_sprites['walls'] = wall_frames

        # 3. Special Sheet for Closed Cells bitmask 15.
        closed_sheet: pygame.Surface = (
            pygame.image.load(f"{basepath}/closed_sheet.png").convert_alpha()
        )
        closed_frames: dict[int, pygame.Surface] = {}
        for i in range(15):
            # Cuts the correct sprite square 48x48
            crop = closed_sheet.subsurface(
                pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
            )
            # Scales to the wished CELL_SIZE
            closed_frames[i] = (
                pygame.transform.scale(crop, (CELL_SIZE, CELL_SIZE))
            )
        self.maze_sprites['closed'] = closed_frames

    def _load_pacman_sprites(self) -> None:
        """Slices sprite sheets into individual surface frames."""
        basepath: str = (
            f"pacman/render/themes/{self.current_theme}/pacman"
        )
        paths: dict[str, str] = {
            'S': f'{basepath}/pacman_B.png',
            'N': f'{basepath}/pacman_C.png',
            'E': f'{basepath}/pacman_D.png',
            'W': f'{basepath}/pacman_E.png',
        }
        for direction, path in paths.items():
            sheet: pygame.Surface = (
                pygame.image.load(path).convert_alpha()
            )
            frames: list[pygame.Surface] = []
            for i in range(3):
                frame: pygame.Surface = sheet.subsurface(
                    pygame.Rect(i * 48, 0, 48, 48)
                )
                scaled: pygame.Surface = pygame.transform.scale(
                    frame, (CELL_SIZE, CELL_SIZE)
                )
                frames.append(scaled)
            self.pac_sprites[direction] = frames

    def draw_pacman(self) -> None:
        """Interpolates pixel points and draws the player texture."""
        col: int = self.engine.pac_col
        row: int = self.engine.pac_row
        dc, dr = DIRECTION_DELTAS[self.engine.pac_dir]
        progress: float = self.engine.pac_move_progress

        x_start, y_start = self.cell_pos(col, row)
        next_col: int = max(0, min(self.cols - 1, col + dc))
        next_row: int = max(0, min(self.rows - 1, row + dr))
        x_end, y_end = self.cell_pos(next_col, next_row)

        x: int = int(x_start + (x_end - x_start) * progress)
        y: int = int(y_start + (y_end - y_start) * progress)

        frame: pygame.Surface = (
            self.pac_sprites
            [self.engine.pac_dir]
            [self.engine.pac_anim_index]
        )
        self.screen.blit(frame, (x, y))
