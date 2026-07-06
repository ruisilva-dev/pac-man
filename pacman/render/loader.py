import pygame
import os
from dataclasses import dataclass
from pacman.constants import (
    SPRITE_SIZE,
    CELL_SIZE,
    GHOST_COLORS,
    DIR_LETTER,
    FALLBACK_THEME,
)


@dataclass
class ThemeAssets:
    """Holds all loaded and sliced sprites for a single theme.

    Attributes:
        pac_frames: Maps a direction key to its list of animation frames.
        death_frames: Maps a direction key to its death animation frames.
        ghost_frames: Maps a color, then a direction, to animation frames.
        scatter_frames: Frightened-state animation frames.
        eaten_sprite: Single sprite shown when a ghost is eaten.
        floor_sprite: Single floor tile sprite.
        wall_frames: Maps a wall bitmask (0-14) to its sprite.
        closed_frames: Maps a closed-cell bitmask (0-14) to its sprite.
        pacgum_sprite: Single standard pacgum sprite.
        superpacgum_frames: Super pacgum animation frames.
    """
    pac_frames: dict[str, list[pygame.Surface]]
    death_frames: dict[str, list[pygame.Surface]]
    ghost_frames: dict[str, dict[str, list[pygame.Surface]]]
    scatter_frames: list[pygame.Surface]
    eaten_sprite: pygame.Surface
    floor_sprite: pygame.Surface
    wall_frames: dict[int, pygame.Surface]
    closed_frames: dict[int, pygame.Surface]
    pacgum_sprite: pygame.Surface
    superpacgum_frames: list[pygame.Surface]


class AssetLoader:
    """Loads, slices, and caches all sprite assets per theme.

    A single instance is created at startup and reused. Each theme is
    loaded once on first request and reused from cache thereafter, so
    repeated themes (e.g. across levels) incur no extra disk I/O.

    Attributes:
        themes_root: Base directory holding all theme folders.
        global_root: Base directory holding menu screen banner and icons.
    """

    def __init__(self, base_path: str) -> None:
        """Initializes the loader with an empty theme cache.

        Args:
            base_path: Root path for the application.
        """
        self.themes_root: str = os.path.join(
            base_path, "pacman", "assets", "textures", "themes"
        )
        self.global_root: str = os.path.join(
            base_path, "pacman", "assets", "textures", "global"
        )
        self._cache: dict[str, ThemeAssets] = {}
        self._ui_cache: dict[str, pygame.Surface] = {}

    def load(self, theme: str) -> ThemeAssets:
        """Returns assets for a theme, loading and caching on first use.

        If the requested theme fails to load, falls back to the classic
        theme so the game can keep running.

        Args:
            theme: Name of the theme folder to load.

        Returns:
            A populated ThemeAssets container.
        """
        if theme in self._cache:
            return self._cache[theme]

        try:
            self._cache[theme] = self._load_theme(theme)
            return self._cache[theme]
        except (pygame.error, FileNotFoundError):
            print(
                f"Warning: theme '{theme}' failed to load. "
                f"Using '{FALLBACK_THEME}'."
            )
            if FALLBACK_THEME not in self._cache:
                self._cache[FALLBACK_THEME] = (
                    self._load_theme(FALLBACK_THEME)
                )
            return self._cache[FALLBACK_THEME]

    def load_ui_icon(self, path: str) -> pygame.Surface:
        """Loads and caches a standalone UI icon, scaled to CELL_SIZE.

        Args:
            path: File system location of the image.

        Returns:
            The scaled surface from cache.
        """
        if path not in self._ui_cache:
            self._ui_cache[path] = self._load_single(path, alpha=True)
        return self._ui_cache[path]

    def _slice_sheet(self, path: str) -> list[pygame.Surface]:
        """Loads a horizontal sprite sheet and slices it into frames.

        Each frame is SPRITE_SIZE wide on the sheet and scaled to
        CELL_SIZE for rendering.

        Args:
            path: File system location of the sprite sheet.

        Returns:
            A list of scaled frame surfaces, left to right.
        """
        sheet: pygame.Surface = pygame.image.load(path).convert_alpha()
        count: int = sheet.get_width() // SPRITE_SIZE
        frames: list[pygame.Surface] = []
        for i in range(count):
            crop = sheet.subsurface(
                pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
            )
            frames.append(
                pygame.transform.scale(crop, (CELL_SIZE, CELL_SIZE))
            )
        return frames

    def _load_single(self, path: str, alpha: bool = True) -> pygame.Surface:
        """Loads one image and scales it to a single cell.

        Args:
            path: File system location of the image.
            alpha: Whether to preserve per-pixel alpha transparency.

        Returns:
            The scaled surface.
        """
        image: pygame.Surface = pygame.image.load(path)
        image = image.convert_alpha() if alpha else image.convert()
        return pygame.transform.scale(image, (CELL_SIZE, CELL_SIZE))

    def _load_theme(self, theme: str) -> ThemeAssets:
        """Loads every asset category for a theme into one container.

        Args:
            theme: Name of the theme folder to load.

        Returns:
            A fully populated ThemeAssets container.
        """
        base: str = f"{self.themes_root}/{theme}"
        return ThemeAssets(
            pac_frames=self._load_pacman(base),
            death_frames=self._load_death(base),
            ghost_frames=self._load_ghosts(base),
            scatter_frames=self._slice_sheet(f"{base}/ghosts/scatter.png"),
            eaten_sprite=self._load_single(f"{base}/ghosts/eaten.png"),
            floor_sprite=self._load_single(
                f"{base}/maze/floor.png", alpha=False
            ),
            wall_frames=self._load_indexed(f"{base}/maze/walls_sheet.png"),
            closed_frames=self._load_indexed(
                f"{base}/maze/closed_sheet.png"
            ),
            pacgum_sprite=self._load_single(f"{base}/pacgums/pacgum.png"),
            superpacgum_frames=self._slice_sheet(
                f"{base}/pacgums/superpacgum_sheet.png"
            ),
        )

    def _load_pacman(self, base: str) -> dict[str, list[pygame.Surface]]:
        """Loads Pac-Man movement frames for all four directions.

        Args:
            base: Theme base directory path.

        Returns:
            A dict mapping each direction key to its frame list.
        """
        frames: dict[str, list[pygame.Surface]] = {}
        for direction, letter in DIR_LETTER.items():
            frames[direction] = self._slice_sheet(
                f"{base}/pacman/pacman_{letter}.png"
            )
        return frames

    def _load_death(self, base: str) -> dict[str, list[pygame.Surface]]:
        """Loads Pac-Man death frames for all four directions.

        Args:
            base: Theme base directory path.

        Returns:
            A dict mapping each direction key to its death frame list.
        """
        frames: dict[str, list[pygame.Surface]] = {}
        for direction, letter in DIR_LETTER.items():
            frames[direction] = self._slice_sheet(
                f"{base}/pacman/pacman_death_{letter}.png"
            )
        return frames

    def _load_ghosts(
        self, base: str
    ) -> dict[str, dict[str, list[pygame.Surface]]]:
        """Loads every ghost color across all four directions.

        Args:
            base: Theme base directory path.

        Returns:
            A nested dict: color -> direction -> frame list.
        """
        ghosts: dict[str, dict[str, list[pygame.Surface]]] = {}
        for color in GHOST_COLORS:
            ghosts[color] = {}
            for direction, letter in DIR_LETTER.items():
                ghosts[color][direction] = self._slice_sheet(
                    f"{base}/ghosts/{color}_{letter}.png"
                )
        return ghosts

    def _load_indexed(self, path: str) -> dict[int, pygame.Surface]:
        """Slices a 15-frame sheet into a bitmask-indexed dictionary.

        Args:
            path: File system location of the sheet (bitmask 0-14).

        Returns:
            A dict mapping bitmask values 0-14 to their sprites.
        """
        frames: list[pygame.Surface] = self._slice_sheet(path)
        return {i: frames[i] for i in range(len(frames))}
