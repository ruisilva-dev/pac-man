import pygame
from pacman.engine import PacmanEngine
from pacman.render.loader import AssetLoader, ThemeAssets
from pacman.render.animator import Animator
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
    ARCADE_W,
    ARCADE_H
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
        world_surface: Render target holding the maze and actors.\
        font: HUD text font.
        assets: The currently active theme's sprite container.
        background_surface: Pre-rendered static maze layer.
        pac_anim: Frame pacing utility for Pac-Man's movement sequence.
        death_anim: Frame pacing utility for Pac-Man's death sequence.
        ghost_anim: Frame pacing utility for the ghosts' wobble animations.
        pacgum_anim: Frame pacing utility for the Super Pacgum animations.
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

        self.font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 20, bold=True
        )

        # Instantiate animators
        self.pac_anim = Animator(PAC_ANIM_SPEED, PAC_ANIM_FRAMES)
        self.death_anim = Animator(PAC_DEATH_ANIM_SPEED, PAC_DEATH_FRAMES)
        # Give placeholder values since set_theme will update them
        self.ghost_anim = Animator(GHOST_ANIM_FPS, 1)
        self.superpacgum_anim = Animator(
            SUPERPACGUM_ANIM_FPS, 1, SUPERPACGUM_ANIM_INTERVAL
        )

        # Bind initial theme; this also renders the background.
        self.assets: ThemeAssets
        self.background_surface: pygame.Surface
        self.set_theme(theme)
        self.img_freeze: pygame.Surface = self.loader.load_ui_icon(
            "pacman/assets/textures/freeze.png"
        )
        self.img_imortal: pygame.Surface = self.loader.load_ui_icon(
            "pacman/assets/textures/imortal.png"
        )
        self.img_speed: pygame.Surface = self.loader.load_ui_icon(
            "pacman/assets/textures/speed.png"
        )

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

        self._render_background()

        # Update existing animators to match the loaded theme asset lengths
        self.ghost_anim.frame_count = len(self.assets.scatter_frames)
        self.ghost_anim.current_frame %= self.ghost_anim.frame_count

        self.superpacgum_anim.frame_count = len(self.assets.superpacgum_frames)
        self.superpacgum_anim.current_frame %= (
            self.superpacgum_anim.frame_count
        )

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

    def draw_pacman(self, dt: float) -> None:
        """Interpolates pixel points and draws the player onto the world.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        self.pac_anim.update(dt)
        x, y = self._interp_pos(
            self.engine.player.col,
            self.engine.player.row,
            self.engine.player.current_dir,
            self.engine.player.move_progress,
        )
        pac_curr_dir: str = self.engine.player.current_dir
        frame: pygame.Surface = (
            self.assets.pac_frames[pac_curr_dir][self.pac_anim.current_frame]
        )
        self.world_surface.blit(frame, (x, y))

    def draw_items(self, dt: float) -> None:
        """Draws all active pacgums and superpacgums onto the world.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        from pacman.items import SuperPacgum
        self.superpacgum_anim.update(dt)

        for row_idx, row in enumerate(self.engine.items):
            for col_idx, item in enumerate(row):
                if item is None:
                    continue
                x, y = self.cell_pos(col_idx, row_idx)
                if isinstance(item, SuperPacgum):
                    self.world_surface.blit(
                        self.assets.superpacgum_frames[
                            self.superpacgum_anim.current_frame
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
        self.ghost_anim.update(dt)

        for i, ghost in enumerate(self.engine.ghosts):
            x, y = self._interp_pos(
                ghost.col, ghost.row, ghost.current_dir, ghost.move_progress
            )

            if ghost.state == "FRIGHTENED":
                frame = self.assets.scatter_frames[
                    self.ghost_anim.current_frame
                ]
            elif ghost.state == "EATEN":
                frame = self.assets.eaten_sprite
            else:
                color = GHOST_COLORS[i % len(GHOST_COLORS)]
                frame = self.assets.ghost_frames[color][ghost.current_dir][
                    self.ghost_anim.current_frame
                ]

            self.world_surface.blit(frame, (x, y))

    def start_death(self) -> None:
        """Resets the death animation to its first frame."""
        self.death_anim.reset()

    def draw_death(self, dt: float) -> None:
        """Advances and draws the death animation onto the world.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        x, y = self._interp_pos(
            self.engine.player.col,
            self.engine.player.row,
            self.engine.player.current_dir,
            self.engine.player.move_progress,
        )

        if self.death_anim.update(dt):
            self.engine.finish_death()
            return

        frame = (
            self.assets.death_frames[self.engine.player.current_dir][
                self.death_anim.current_frame
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
        icon_size = self.img_imortal.get_width()  # Será 48 (CELL_SIZE)
        spacing = 16  # Espaço horizontal entre os ícones
        total_w = (3 * icon_size) + (2 * spacing)

        # Centralizar horizontalmente no ecrã do arcade
        start_x = (ARCADE_W - total_w) // 2

        # Centralizar verticalmente dentro do espaço da barra preta inferior
        start_y = (ARCADE_H - HUD_BAR_H) + (HUD_BAR_H - icon_size) // 2

        # Mapeamento com base no estado atual da engine (self.engine)
        cheats = [
            (self.img_freeze, self.engine.cheat_freeze, 0),
            (self.img_imortal, self.engine.cheat_invincible, 1),
            (self.img_speed, self.engine.cheat_speed, 2)
        ]

        for img, is_active, index in cheats:
            if is_active:
                # Desenha o ícone fixo sem qualquer verificação de tempo/piscar
                x_pos = start_x + index * (icon_size + spacing)
                target.blit(img, (x_pos, start_y))
