from typing import TYPE_CHECKING
import pygame
from pacman.config import Configuration
from pacman.render.loader import AssetLoader
from pacman.highscores import HighscoreManager
from pacman.constants import FPS, ARCADE_W, ARCADE_H, BG_COLOR


if TYPE_CHECKING:
    from pacman.scenes.base import Scene


class Game:
    """Owns the window, the main loop, and the active scene.

    The Game holds resources shared across scenes (the asset loader and
    the highscore manager), the fixed arcade surface every scene draws
    onto, and performs the single final scale from arcade to window. It
    delegates input, update, and drawing to whichever scene is active,
    and lets scenes swap themselves out via change_scene.

    Attributes:
        config: The loaded game configuration.
        loader: Shared asset loader with per-theme caching.
        theme_overridden: Flag tracking if manual theme selection occurred.
        highscores: Shared leaderboard manager.
        window: The real window surface sized from configuration.
        arcade_surface: Fixed virtual screen every scene draws onto.
        clock: Frame scheduler.
        running: Whether the main loop is active.
        scene: The currently active scene.
    """

    def __init__(self, config: Configuration, config_path: str) -> None:
        """Initializes shared resources and starts at the menu.

        Args:
            config: The loaded game configuration.
            config_path: Path the config was loaded from (for highscore
                path sanitization).
        """
        pygame.init()
        self.config: Configuration = config

        # Display must exist before any convert_alpha() on loaded sprites.
        self.window: pygame.Surface = pygame.display.set_mode(
            (config.window_width, config.window_height)
        )
        pygame.display.set_caption("Pac-Man")

        self.loader: AssetLoader = AssetLoader()

        self.theme_overridden: bool = False

        self.highscores: HighscoreManager = HighscoreManager(
            config.highscore_filename, config_path
        )
        self.highscores.load_from_disk()

        self.arcade_surface: pygame.Surface = pygame.Surface(
            (ARCADE_W, ARCADE_H)
        )
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = False

        # Start at the main menu.
        from pacman.scenes.menu import MenuScene
        self.scene: "Scene" = MenuScene(self)

    def change_scene(self, scene: "Scene") -> None:
        """Replaces the active scene.

        Args:
            scene: The scene to make active.
        """
        self.scene = scene

    def _present(self) -> None:
        """Scales the arcade surface to fit the window, preserving aspect."""
        win_w: int = self.window.get_width()
        win_h: int = self.window.get_height()

        # Fractional scale that fits, preserving aspect ratio.
        scale: float = min(win_w / ARCADE_W, win_h / ARCADE_H)
        scaled_w: int = int(ARCADE_W * scale)
        scaled_h: int = int(ARCADE_H * scale)
        scaled = pygame.transform.smoothscale(
            self.arcade_surface, (scaled_w, scaled_h)
        )

        x: int = (win_w - scaled_w) // 2
        y: int = (win_h - scaled_h) // 2
        self.window.fill(BG_COLOR)
        self.window.blit(scaled, (x, y))

    def run(self) -> None:
        """Runs the main loop, delegating to the active scene."""
        self.running = True

        while self.running:
            dt: float = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.arcade_surface)
            self._present()
            pygame.display.flip()

        pygame.quit()
