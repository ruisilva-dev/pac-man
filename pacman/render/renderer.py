import pygame
from pacman.engine import PacmanEngine
from pacman.render.loader import AssetLoader, ThemeAssets
from pacman.constants import (
    DIRECTION_DELTAS,
    DIRECTION_BITS,
    CELL_SIZE,
    PAC_ANIM_SPEED,
    PAC_ANIM_FRAMES,
    PAC_DEATH_ANIM_SPEED,
    PAC_DEATH_FRAMES,
    GHOST_ANIM_FPS,
    SUPERPACGUM_ANIM_FPS,
    SUPERPACGUM_ANIM_INTERVAL,
    HUD_BAR_H,
    GHOST_COLORS,
)

# HUD text color
HUD_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)


class GameRenderer:
    """Draws the game onto a world surface sized to the maze.

    The renderer draws only the maze and its actors onto a world
    surface whose size equals the current level (cols x rows of
    CELL_SIZE), with no HUD and no scaling. Composition of the HUD
    bars, centering, and final scaling to the window is handled by the
    Game pipeline. The HUD is drawn onto a caller-provided surface so
    it can live in the fixed arcade bars rather than scaling with the
    maze.

    Attributes:
        engine: Shared logic core engine reference.
        loader: Shared asset loader providing cached theme assets.
        grid: Nested integer sequence modeling active layout bitmasks.
        rows: Total row count of the grid.
        cols: Total column count of the grid.
        world_width: World surface width in pixels (maze only).
        world_height: World surface height in pixels (maze only).
        world_surface: Render target holding the maze and actors.
        ghost_anim_index: Current visual frame index for ghost animation.
        ghost_anim_timer: Frame pacing accumulator for ghosts.
        pac_anim_index: Current visual frame index for Pac-Man movement.
        pac_anim_timer: Frame pacing accumulator for Pac-Man.
        death_anim_index: Current visual frame index for the death sequence.
        death_anim_timer: Frame pacing accumulator for the death sequence.
        superpacgum_anim_index: Visual frame index for power pellets.
        superpacgum_anim_timer: Frame pacing accumulator for power pellets.
        superpacgum_wait_timer: Pause duration between pellet flashes.
        font: HUD text font.
        assets: The currently active theme's sprite container.
        background_surface: Pre-rendered static maze layer.
    """

    def __init__(
        self,
        engine: PacmanEngine,
        loader: AssetLoader,
        theme: str = "classic",
    ) -> None:
        """Initializes the world surface and binds the first theme.

        Args:
            engine: Shared logic core engine reference.
            loader: Shared asset loader providing cached theme assets.
            theme: Name of the theme to load initially.
        """
        self.engine: PacmanEngine = engine
        self.loader: AssetLoader = loader
        self.grid: list[list[int]] = self.engine.grid
        self.rows: int = len(self.grid)
        self.cols: int = len(self.grid[0]) if self.rows > 0 else 0

        # World surface is the maze only, at its natural size.
        self.world_width: int = self.cols * CELL_SIZE
        self.world_height: int = self.rows * CELL_SIZE
        self.world_surface: pygame.Surface = pygame.Surface(
            (self.world_width, self.world_height)
        )

        # Rendering state - animation timers and frame indices
        self.ghost_anim_index: int = 0
        self.ghost_anim_timer: float = 0.0
        self.pac_anim_index: int = 0
        self.pac_anim_timer: float = 0.0
        self.death_anim_index: int = 0
        self.death_anim_timer: float = 0.0
        self.superpacgum_anim_index: int = 0
        self.superpacgum_anim_timer: float = 0.0
        self.superpacgum_wait_timer: float = 0.0

        self.font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 20, bold=True
        )

        # Bind initial theme; this also renders the background.
        self.assets: ThemeAssets
        self.background_surface: pygame.Surface
        self.set_theme(theme)

    def set_theme(self, theme: str) -> None:
        """Switches the active theme and re-renders the static maze.

        Args:
            theme: Name of the theme to activate.
        """
        self.assets = self.loader.load(theme)

        self.grid = self.engine.grid
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0

        self.world_width = self.cols * CELL_SIZE
        self.world_height = self.rows * CELL_SIZE
        self.world_surface = pygame.Surface(
            (self.world_width, self.world_height)
        )

        self.background_surface = pygame.Surface(
            (self.world_width, self.world_height)
        )

        self.superpacgum_anim_index = 0
        self.superpacgum_anim_timer = 0.0
        self.superpacgum_wait_timer = 0.0

        self._render_background()

    def cell_pos(self, col: int, row: int) -> tuple[int, int]:
        """Calculates top-left world pixel position for a grid cell.

        Args:
            col: Grid column index.
            row: Grid row index.

        Returns:
            A tuple of (x, y) pixel coordinates within the world surface.
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

    def _closed_bitmask(self, row_idx: int, col_idx: int) -> int:
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
        """Pre-renders the maze tiles onto the background surface."""
        floor: pygame.Surface = self.assets.floor_sprite
        wall_frames: dict[int, pygame.Surface] = self.assets.wall_frames
        closed_frames: dict[int, pygame.Surface] = self.assets.closed_frames

        for row_idx, row in enumerate(self.grid):
            for col_idx, cell_value in enumerate(row):
                x, y = self.cell_pos(col_idx, row_idx)

                # 1. Floor in all the cells
                self.background_surface.blit(floor, (x, y))

                # 2. Normal wall or closed cell
                if cell_value == 15:
                    closed = self._closed_bitmask(row_idx, col_idx)
                    if closed in closed_frames:
                        self.background_surface.blit(
                            closed_frames[closed], (x, y)
                        )
                elif cell_value in wall_frames:
                    self.background_surface.blit(
                        wall_frames[cell_value], (x, y)
                    )

    def draw_grid(self) -> None:
        """Blits the pre-rendered background onto the world surface."""
        self.world_surface.blit(self.background_surface, (0, 0))

    def _interp_pos(
        self, col: int, row: int, direction: str, progress: float
    ) -> tuple[int, int]:
        """Interpolates an actor's pixel position between two cells.

        Args:
            col: Current grid column.
            row: Current grid row.
            direction: Movement direction key.
            progress: Movement interpolation progress (0.0 to 1.0).

        Returns:
            The interpolated (x, y) pixel coordinates in world space.
        """
        dc, dr = DIRECTION_DELTAS[direction]
        x_start, y_start = self.cell_pos(col, row)
        next_col: int = max(0, min(self.cols - 1, col + dc))
        next_row: int = max(0, min(self.rows - 1, row + dr))
        x_end, y_end = self.cell_pos(next_col, next_row)
        x: int = int(x_start + (x_end - x_start) * progress)
        y: int = int(y_start + (y_end - y_start) * progress)
        return (x, y)

    def _update_pac_anim(self, dt: float) -> None:
        """Advances the Pac-Man movement animation frame.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        self.pac_anim_timer += dt * PAC_ANIM_SPEED
        if self.pac_anim_timer >= 1.0:
            self.pac_anim_timer -= 1.0
            self.pac_anim_index = (
                (self.pac_anim_index + 1) % PAC_ANIM_FRAMES
            )

    def draw_pacman(self, dt: float) -> None:
        """Interpolates pixel points and draws the player onto the world.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        self._update_pac_anim(dt)
        x, y = self._interp_pos(
            self.engine.pac_col,
            self.engine.pac_row,
            self.engine.pac_dir,
            self.engine.pac_move_progress,
        )
        frame: pygame.Surface = (
            self.assets.pac_frames[self.engine.pac_dir][self.pac_anim_index]
        )
        self.world_surface.blit(frame, (x, y))

    def draw_items(self, dt: float) -> None:
        """Draws all active pacgums and superpacgums onto the world.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        from pacman.items import SuperPacgum

        # Advance the super pacgum animation (with wait between cycles)
        if self.superpacgum_wait_timer > 0.0:
            self.superpacgum_wait_timer -= dt
        else:
            self.superpacgum_anim_timer += dt * SUPERPACGUM_ANIM_FPS
            if self.superpacgum_anim_timer >= 1.0:
                self.superpacgum_anim_timer = 0.0
                self.superpacgum_anim_index = (
                    (self.superpacgum_anim_index + 1)
                    % len(self.assets.superpacgum_frames)
                )
                if self.superpacgum_anim_index == 0:
                    self.superpacgum_wait_timer = SUPERPACGUM_ANIM_INTERVAL

        for row_idx, row in enumerate(self.engine.items):
            for col_idx, item in enumerate(row):
                if item is None:
                    continue
                x, y = self.cell_pos(col_idx, row_idx)
                if isinstance(item, SuperPacgum):
                    self.world_surface.blit(
                        self.assets.superpacgum_frames[
                            self.superpacgum_anim_index
                        ],
                        (x, y)
                    )
                else:
                    self.world_surface.blit(
                        self.assets.pacgum_sprite, (x, y)
                    )

    def draw_ghosts(self, dt: float) -> None:
        """Interpolates and draws all ghosts onto the world surface.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        # Advance the shared ghost animation
        self.ghost_anim_timer += dt * GHOST_ANIM_FPS
        if self.ghost_anim_timer >= 1.0:
            self.ghost_anim_timer -= 1.0
            self.ghost_anim_index = (
                (self.ghost_anim_index + 1)
                % len(self.assets.scatter_frames)
            )

        for i, ghost in enumerate(self.engine.ghosts):
            x, y = self._interp_pos(
                ghost.col, ghost.row, ghost.current_dir, ghost.move_progress
            )

            if ghost.state == "FRIGHTENED":
                frame = self.assets.scatter_frames[self.ghost_anim_index]
            elif ghost.state == "EATEN":
                frame = self.assets.eaten_sprite
            else:
                color = GHOST_COLORS[i % len(GHOST_COLORS)]
                frame = self.assets.ghost_frames[color][ghost.current_dir][
                    self.ghost_anim_index
                ]

            self.world_surface.blit(frame, (x, y))

    def start_death(self) -> None:
        """Resets the death animation to its first frame."""
        self.death_anim_index = 0
        self.death_anim_timer = 0.0

    def draw_death(self, dt: float) -> None:
        """Advances and draws the death animation onto the world.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        x, y = self._interp_pos(
            self.engine.pac_col,
            self.engine.pac_row,
            self.engine.pac_dir,
            self.engine.pac_move_progress,
        )

        self.death_anim_timer += dt * PAC_DEATH_ANIM_SPEED
        if self.death_anim_timer >= 1.0:
            self.death_anim_timer -= 1.0
            self.death_anim_index += 1
            if self.death_anim_index >= PAC_DEATH_FRAMES:
                self.death_anim_index = 0
                self.engine.finish_death()
                return

        frame = (
            self.assets.death_frames[self.engine.pac_dir][
                self.death_anim_index
            ]
        )
        self.world_surface.blit(frame, (x, y))

    def draw_hud(self, target: pygame.Surface, highscore: int) -> None:
        """Draws the HUD onto a target surface at fixed bar positions.

        The top bar shows the high score centered; the bottom bar shows
        remaining lives on the left and the current score on the right.

        Args:
            target: Surface to draw the HUD onto (the arcade surface).
            highscore: The leaderboard's best score, shown at the top.
        """
        target_w: int = target.get_width()
        target_h: int = target.get_height()

        # Top bar: centered high score
        lvl_text = self.font.render(
            f"LEVEL {self.engine.level}", True, HUD_TEXT_COLOR
        )
        target.blit(lvl_text, (CELL_SIZE // 4, (HUD_BAR_H - 20) // 2))

        hs_text = self.font.render(
            f"HIGH SCORE {highscore:06d}", True, HUD_TEXT_COLOR
        )
        hs_rect = hs_text.get_rect(center=(target_w // 2, HUD_BAR_H // 2))
        target.blit(hs_text, hs_rect)

        time_val = max(0, int(self.engine.level_timer))
        time_text = self.font.render(
            f"TIME {time_val:02d}", True, HUD_TEXT_COLOR
        )
        time_rect = time_text.get_rect(
            midright=(target_w - CELL_SIZE // 4, HUD_BAR_H // 2)
        )
        target.blit(time_text, time_rect)

        # Bottom bar: lives on the left, score on the right
        bottom_y: int = target_h - HUD_BAR_H
        life_frame: pygame.Surface = self.assets.pac_frames['E'][1]
        for i in range(self.engine.lives):
            x = i * CELL_SIZE + CELL_SIZE // 4
            y = bottom_y + (HUD_BAR_H - CELL_SIZE) // 2
            target.blit(life_frame, (x, y))

        score_text = self.font.render(
            f"{self.engine.score:06d}", True, HUD_TEXT_COLOR
        )
        score_rect = score_text.get_rect(
            midright=(target_w - CELL_SIZE // 4, bottom_y + HUD_BAR_H // 2)
        )
        target.blit(score_text, score_rect)
