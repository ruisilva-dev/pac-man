import pygame
from pacman.engine import PacmanEngine, DIRECTION_DELTAS

# Cell dimensions and geometric offset properties
CELL_SIZE: int = 48
BIT_N: int = 1
BIT_E: int = 2
BIT_S: int = 4
BIT_W: int = 8

# Structural line dimensions
WALL_THICKNESS: int = 6
WALL_OFFSET: int = WALL_THICKNESS // 2
CORNERS: int = WALL_OFFSET - 1

# Structural sprite dimensions
SPRITE_OFFSET: int = WALL_OFFSET + 1

# Color definitions
WALL_COLOR: tuple[int, int, int] = (33, 33, 255)
BG_COLOR: tuple[int, int, int] = (0, 0, 0)
TEXT_COLOR: tuple[int, int, int] = (150, 150, 150)

# Environment configuration constraints
FONT_SIZE: int = 24
FPS: int = 60


class GameRenderer:
    """Manages graphical rendering operations using Pygame surfaces.

    Attributes:
        engine: Shared logic configuration state source container.
        grid: Nested integer sequence modeling active layout bitmasks.
        rows: Map tracking total row constraints.
        cols: Map tracking total column constraints.
        width: Calculated pixel dimensions tracking surface width.
        height: Calculated pixel dimensions tracking surface height.
        screen: Render target interface via display drivers.
        font: Internal text style engine tracking font properties.
        pac_sprites: Categorized collection matching direction keys to
            textures.
    """

    def __init__(self, engine: PacmanEngine) -> None:
        """Initializes window and loads graphical assets.

        Args:
            engine: Shared logic core engine reference.
        """
        pygame.init()
        self.engine: PacmanEngine = engine
        self.grid: list[list[int]] = self.engine.grid
        self.rows: int = len(self.grid)
        self.cols: int = len(self.grid[0]) if self.rows > 0 else 0
        self.width: int = self.cols * CELL_SIZE + WALL_THICKNESS
        self.height: int = self.rows * CELL_SIZE + WALL_THICKNESS
        self.screen: pygame.Surface = (
            pygame.display.set_mode((self.width, self.height))
        )
        pygame.display.set_caption("Pac-Man - Wall and Number Debug Window")

        self.pac_sprites: dict[str, list[pygame.Surface]] = {}
        self._load_sprites()

        self.font: pygame.font.Font = (
            pygame.font.SysFont(None, FONT_SIZE)
        )

    def cell_pos(self, col: int, row: int) -> tuple[int, int]:
        """Calculates origin corner screen pixels for a grid cell.

        Args:
            col: Grid matrix X index targeting selected cell location.
            row: Grid matrix Y index targeting selected cell location.

        Returns:
            A tuple mapping corresponding (X, Y) pixel coordinates.
        """
        return (
            col * CELL_SIZE + WALL_OFFSET,
            row * CELL_SIZE + WALL_OFFSET
        )

    def cell_center(self, x: int, y: int) -> tuple[int, int]:
        """Calculates center pixel positions from an origin pair.

        Args:
            x: Target horizontal pixel coordinate point.
            y: Target vertical pixel coordinate point.

        Returns:
            A tuple tracking centered coordinate midpoints.
        """
        return (
            x + CELL_SIZE // 2,
            y + CELL_SIZE // 2
        )

    def draw_grid(self) -> None:
        """Renders the maze walls and spatial values to the screen."""
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell_value in enumerate(row):
                x, y = self.cell_pos(col_idx, row_idx)
                center_x, center_y = self.cell_center(x, y)
                is_closed: bool = cell_value == 15

                # 1. Geometry drawing blocks tracking North lines
                if cell_value & BIT_N:
                    neighbor = (
                        self.grid[row_idx - 1][col_idx]
                        if row_idx > 0 else None
                    )
                    if not (is_closed and neighbor == 15):
                        pygame.draw.line(
                            self.screen, WALL_COLOR,
                            (x - CORNERS, y),
                            (x + CELL_SIZE + CORNERS, y),
                            WALL_THICKNESS
                        )
                # East line layout processing configurations
                if cell_value & BIT_E:
                    neighbor = (
                        self.grid[row_idx][col_idx + 1]
                        if col_idx < self.cols - 1 else None
                    )
                    if not (is_closed and neighbor == 15):
                        pygame.draw.line(
                            self.screen, WALL_COLOR,
                            (x + CELL_SIZE, y - CORNERS),
                            (
                                x + CELL_SIZE,
                                y + CELL_SIZE + CORNERS
                            ),
                            WALL_THICKNESS
                        )
                # South line layout processing configurations
                if cell_value & BIT_S:
                    neighbor = (
                        self.grid[row_idx + 1][col_idx]
                        if row_idx < self.rows - 1 else None
                    )
                    if not (is_closed and neighbor == 15):
                        pygame.draw.line(
                            self.screen, WALL_COLOR,
                            (x - CORNERS, y + CELL_SIZE),
                            (
                                x + CELL_SIZE + CORNERS,
                                y + CELL_SIZE
                            ),
                            WALL_THICKNESS
                        )
                # West line layout processing configurations
                if cell_value & BIT_W:
                    neighbor = (
                        self.grid[row_idx][col_idx - 1]
                        if col_idx > 0 else None
                    )
                    if not (is_closed and neighbor == 15):
                        pygame.draw.line(
                            self.screen, WALL_COLOR,
                            (x, y - CORNERS),
                            (x, y + CELL_SIZE + CORNERS),
                            WALL_THICKNESS
                        )

                # 2. Render internal cell encoding values
                text_surface: pygame.Surface = (
                    self.font.render(
                        str(cell_value), True, TEXT_COLOR
                    )
                )
                text_rect: pygame.Rect = (
                    text_surface.get_rect(
                        center=(center_x, center_y)
                    )
                )
                self.screen.blit(text_surface, text_rect)

        # 3. Outer border frame structure
        pygame.draw.rect(
            self.screen, WALL_COLOR,
            (0, 0, self.width, self.height), WALL_THICKNESS
        )

    def _load_sprites(self) -> None:
        """Slices sprite sheets into individual surface frames."""
        paths: dict[str, str] = {
            'S': 'pacman/render/sprites/pacman_samuraiB.png',
            'N': 'pacman/render/sprites/pacman_samuraiC.png',
            'E': 'pacman/render/sprites/pacman_samuraiD.png',
            'W': 'pacman/render/sprites/pacman_samuraiE.png',
        }
        for direction, path in paths.items():
            sheet: pygame.Surface = (
                pygame.image.load(path).convert_alpha()
            )
            frames: list[pygame.Surface] = []
            for i in range(3):
                frame: pygame.Surface = sheet.subsurface(
                    pygame.Rect(i * 20, 0, 20, 20)
                )
                scaled: pygame.Surface = pygame.transform.scale(
                    frame, (CELL_SIZE - WALL_THICKNESS,
                            CELL_SIZE - WALL_THICKNESS)
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

        x: int = int(x_start + (x_end - x_start) * progress) + SPRITE_OFFSET
        y: int = int(y_start + (y_end - y_start) * progress) + SPRITE_OFFSET

        frame: pygame.Surface = (
            self.pac_sprites
            [self.engine.pac_dir]
            [self.engine.pac_anim_index]
        )
        self.screen.blit(frame, (x, y))
