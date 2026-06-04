import pygame
from pacman.engine import PacmanEngine
from pacman.constants import (
    DIRECTION_DELTAS,
    DIRECTION_BITS,
    SPRITE_SIZE,
    CELL_SIZE,
    PAC_ANIM_SPEED,
    PAC_ANIM_FRAMES,
    PAC_DEATH_ANIM_SPEED,
    PAC_DEATH_FRAMES,
    GHOST_ANIM_FPS,
    SUPERPACGUM_ANIM_FPS,
    SUPERPACGUM_ANIM_INTERVAL,
    HUD_HEIGHT,
)


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
        self.height: int = self.rows * CELL_SIZE + HUD_HEIGHT * 2
        self.screen: pygame.Surface = (
            pygame.display.set_mode((self.width, self.height))
        )
        pygame.display.set_caption("Pac-Man")

        self.pac_sprites: dict[str, list[pygame.Surface]] = {}
        self.death_sprites: dict[str, list[pygame.Surface]] = {}
        self.floor_sprite: pygame.Surface
        self.maze_sprites: dict[
            str, dict[int, pygame.Surface]
        ] = {}
        self.ghost_sprites: dict[str, dict[str, list[pygame.Surface]]] = {}
        self.scatter_frames: list[pygame.Surface] = []
        self.eaten_sprite: pygame.Surface
        self.ghost_anim_index: int = 0
        self.ghost_anim_timer: float = 0.0
        self.pac_anim_index: int = 0
        self.pac_anim_timer: float = 0.0
        self.death_anim_index: int = 0
        self.death_anim_timer: float = 0.0
        self.superpacgum_anim_index: int = 0
        self.superpacgum_anim_timer: float = 0.0
        self.superpacgum_wait_timer: float = 0.0
        self._load_sprites()
        self.font: pygame.font.Font = pygame.font.SysFont("monospace",
                                                          20, bold=True)
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
        return (col * CELL_SIZE, row * CELL_SIZE + HUD_HEIGHT)

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
            effective &= ~DIRECTION_BITS["N"]
        if (col_idx < self.cols - 1
                and self.grid[row_idx][col_idx + 1] == 15):
            effective &= ~DIRECTION_BITS["E"]
        if (row_idx < self.rows - 1
                and self.grid[row_idx + 1][col_idx] == 15):
            effective &= ~DIRECTION_BITS["S"]
        if col_idx > 0 and self.grid[row_idx][col_idx - 1] == 15:
            effective &= ~DIRECTION_BITS["W"]
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
        self._load_ghost_sprites()
        self._load_maze_sprites()
        self._load_pacgum_sprites()

    def _load_pacgum_sprites(self) -> None:
        """Loads pacgum and superpacgum sprites."""
        basepath: str = (
            f"pacman/render/themes/{self.current_theme}/pacgums"
        )
        pacgum = pygame.image.load(
            f"{basepath}/pacgum.png"
        ).convert_alpha()
        self.pacgum_sprite: pygame.Surface = (
            pygame.transform.scale(pacgum, (CELL_SIZE, CELL_SIZE))
        )

        sheet: pygame.Surface = pygame.image.load(
            f"{basepath}/superpacgum_sheet.png"
        ).convert_alpha()
        frame_count: int = sheet.get_width() // SPRITE_SIZE
        self.superpacgum_frames: list[pygame.Surface] = []
        for i in range(frame_count):
            crop = sheet.subsurface(
                pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
            )
            self.superpacgum_frames.append(
                pygame.transform.scale(crop, (CELL_SIZE, CELL_SIZE))
            )

    def _load_ghost_sprites(self) -> None:
        """Loads all ghost sprites by color, direction, and state."""
        basepath: str = (
            f"pacman/render/themes/{self.current_theme}/ghosts"
        )
        colors: list[str] = ['red', 'pink', 'orange', 'blue']
        dirs: dict[str, str] = {'S': 'b', 'N': 'c', 'E': 'd', 'W': 'e'}

        for color in colors:
            self.ghost_sprites[color] = {}
            for direction, suffix in dirs.items():
                sheet = pygame.image.load(
                    f"{basepath}/{color}_{suffix}.png"
                ).convert_alpha()
                frame_count: int = sheet.get_width() // SPRITE_SIZE
                frames: list[pygame.Surface] = []
                for i in range(frame_count):
                    crop = sheet.subsurface(
                        pygame.Rect(i * SPRITE_SIZE, 0,
                                    SPRITE_SIZE, SPRITE_SIZE)
                    )
                    frames.append(
                        pygame.transform.scale(crop, (CELL_SIZE, CELL_SIZE))
                    )
                self.ghost_sprites[color][direction] = frames

        # Scatter (FRIGHTENED) — sheet animado
        scatter_sheet = pygame.image.load(
            f"{basepath}/scatter.png"
        ).convert_alpha()
        frame_count = scatter_sheet.get_width() // SPRITE_SIZE
        for i in range(frame_count):
            crop = scatter_sheet.subsurface(
                pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
            )
            self.scatter_frames.append(
                pygame.transform.scale(crop, (CELL_SIZE, CELL_SIZE))
            )

        # Eaten — imagem estática
        eaten = pygame.image.load(
            f"{basepath}/eaten.png"
        ).convert_alpha()
        self.eaten_sprite = (
            pygame.transform.scale(eaten, (CELL_SIZE, CELL_SIZE))
        )

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
        death_paths: dict[str, str] = {
            'S': f'{basepath}/pacman_death_B.png',
            'N': f'{basepath}/pacman_death_C.png',
            'E': f'{basepath}/pacman_death_D.png',
            'W': f'{basepath}/pacman_death_E.png',
        }
        for direction, path in paths.items():
            sheet: pygame.Surface = (
                pygame.image.load(path).convert_alpha()
            )
            frames: list[pygame.Surface] = []
            for i in range(3):
                frame: pygame.Surface = sheet.subsurface(
                    pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
                )
                scaled: pygame.Surface = pygame.transform.scale(
                    frame, (CELL_SIZE, CELL_SIZE)
                )
                frames.append(scaled)
            self.pac_sprites[direction] = frames
        for direction, path in death_paths.items():
            sheet = pygame.image.load(path).convert_alpha()
            frames = []
            for i in range(PAC_DEATH_FRAMES):
                crop = sheet.subsurface(
                    pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
                )
                frames.append(pygame.transform.scale(crop, (CELL_SIZE,
                                                            CELL_SIZE)))
            self.death_sprites[direction] = frames

    def _update_pac_anim(self, dt: float) -> None:
        """
        Advances the Pac-Man animation frame.
        pac_anim_index: Current visual frame animation index offset.
        pac_anim_timer: Elapsed delta accumulator scaling game
            animation frames.
        """
        self.pac_anim_timer += dt * PAC_ANIM_SPEED
        if self.pac_anim_timer >= 1.0:
            self.pac_anim_timer -= 1.0
            self.pac_anim_index = (
                (self.pac_anim_index + 1) % PAC_ANIM_FRAMES
            )

    def draw_hud(self) -> None:
        """
        Draws the HUD - Highscore on top, lives and score on bottom.
        """
        # Bar on top: centered high score
        hs_text = self.font.render(
            f"HIGH SCORE {0:06d}",
            True, (255, 255, 255)
        )
        hs_rect = hs_text.get_rect(center=(self.width // 2, HUD_HEIGHT // 2))
        self.screen.blit(hs_text, hs_rect)
        # Bar on the Bottom: lives and current score
        bottom_y: int = self.rows * CELL_SIZE + HUD_HEIGHT
        life_frame: pygame.Surface = self.pac_sprites['E'][1]
        for i in range(self.engine.lives):
            x = i * CELL_SIZE + CELL_SIZE // 4
            y = bottom_y + (HUD_HEIGHT - CELL_SIZE) // 2
            self.screen.blit(life_frame, (x, y))
        score_text = self.font.render(
            f"{self.engine.score:06d}", True, (255, 255, 255)
        )
        score_rect = score_text.get_rect(
            midright=(self.width - CELL_SIZE // 4,
                      bottom_y + HUD_HEIGHT // 2)
        )
        self.screen.blit(score_text, score_rect)

    def draw_pacman(self, dt: float) -> None:
        """Interpolates pixel points and draws the player texture."""
        self._update_pac_anim(dt)
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
            [self.pac_anim_index]
        )
        self.screen.blit(frame, (x, y))

    def draw_items(self, dt: float) -> None:
        """Draws all active pacgums and superpacgums on the screen."""
        from pacman.items import SuperPacgum
        if self.superpacgum_wait_timer > 0.0:
            self.superpacgum_wait_timer -= dt
        # Advance superpacgum animation
        else:
            self.superpacgum_anim_timer += dt * SUPERPACGUM_ANIM_FPS
            if self.superpacgum_anim_timer >= 1:
                self.superpacgum_anim_timer = 0
                self.superpacgum_anim_index = (
                    (self.superpacgum_anim_index + 1)
                    % len(self.superpacgum_frames)
                )
                if self.superpacgum_anim_index == 0:
                    self.superpacgum_wait_timer = SUPERPACGUM_ANIM_INTERVAL

        for row_idx, row in enumerate(self.engine.items):
            for col_idx, item in enumerate(row):
                if item is None:
                    continue
                x, y = self.cell_pos(col_idx, row_idx)
                if isinstance(item, SuperPacgum):
                    self.screen.blit(
                        self.superpacgum_frames[self.superpacgum_anim_index],
                        (x, y)
                    )
                else:
                    self.screen.blit(self.pacgum_sprite, (x, y))

    def draw_ghosts(self, dt: float) -> None:
        """Interpolates and draws all ghost sprites."""
        colors: list[str] = ['red', 'pink', 'orange', 'blue']

        # Avançar animação do scatter
        self.ghost_anim_timer += dt * GHOST_ANIM_FPS
        if self.ghost_anim_timer >= 1.0:
            self.ghost_anim_timer -= 1.0
            self.ghost_anim_index = (
                (self.ghost_anim_index + 1) % len(self.scatter_frames)
            )

        for i, ghost in enumerate(self.engine.ghosts):
            dc, dr = DIRECTION_DELTAS[ghost.current_dir]
            progress: float = ghost.move_progress

            x_start, y_start = self.cell_pos(ghost.col, ghost.row)
            next_col: int = max(0, min(self.cols - 1, ghost.col + dc))
            next_row: int = max(0, min(self.rows - 1, ghost.row + dr))
            x_end, y_end = self.cell_pos(next_col, next_row)

            x: int = int(x_start + (x_end - x_start) * progress)
            y: int = int(y_start + (y_end - y_start) * progress)

            if ghost.state == "FRIGHTENED":
                frame = self.scatter_frames[self.ghost_anim_index]
            elif ghost.state == "EATEN":
                frame = self.eaten_sprite
            else:
                color = colors[i % len(colors)]
                frame = (self.ghost_sprites[color][ghost.current_dir]
                         [self.ghost_anim_index])

            self.screen.blit(frame, (x, y))

    def start_death(self) -> None:
        """Captures the current animation frame as the death start point."""
        self.death_anim_index = self.pac_anim_index
        self.death_anim_timer = 0.0

    def draw_death(self, dt: float) -> None:
        """Advances and draws the death animation, freezing the game."""
        col, row = self.engine.pac_col, self.engine.pac_row
        dc, dr = DIRECTION_DELTAS[self.engine.pac_dir]
        progress = self.engine.pac_move_progress

        x_start, y_start = self.cell_pos(col, row)
        next_col = max(0, min(self.cols - 1, col + dc))
        next_row = max(0, min(self.rows - 1, row + dr))
        x_end, y_end = self.cell_pos(next_col, next_row)

        x = int(x_start + (x_end - x_start) * progress)
        y = int(y_start + (y_end - y_start) * progress)

        self.death_anim_timer += dt * PAC_DEATH_ANIM_SPEED
        if self.death_anim_timer >= 1.0:
            self.death_anim_timer -= 1.0
            self.death_anim_index += 1
            if self.death_anim_index >= PAC_DEATH_FRAMES:
                self.death_anim_index = 0
                self.engine.finish_death()
                return

        frame = self.death_sprites[self.engine.pac_dir][self.death_anim_index]
        self.screen.blit(frame, (x, y))
