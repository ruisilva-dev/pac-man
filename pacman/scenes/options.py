from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.constants import ARCADE_W, ARCADE_H, BG_COLOR, AVAILABLE_THEMES

if TYPE_CHECKING:
    from pacman.game import Game

TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
LABEL_COLOR: tuple[int, int, int] = (255, 255, 255)
VALUE_COLOR: tuple[int, int, int] = (255, 255, 0)
HINT_COLOR: tuple[int, int, int] = (180, 180, 180)


class OptionsScene(Scene):
    """Lets the player cycle the active theme.

    Changing the theme updates the shared configuration so subsequent
    gameplay scenes load the chosen theme.

    Attributes:
        game: Back-reference to the coordinating Game.
        previous_scene: The caller scene to return to upon exiting.
        theme_index: Index into AVAILABLE_THEMES for the current theme.
        title_font: Font for the heading.
        item_font: Font for the option rows.
        hint_font: Font for the navigation hint.
    """

    def __init__(self, game: "Game", previous_scene: Scene) -> None:
        """Initializes the options screen at the current theme.

        Args:
            game: The coordinating Game instance.
        """
        super().__init__(game)
        self.previous_scene = previous_scene
        current = game.config.theme
        self.theme_index: int = (
            AVAILABLE_THEMES.index(current)
            if current in AVAILABLE_THEMES else 0
        )
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 56, bold=True
        )
        self.item_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 36, bold=True
        )
        self.hint_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 24, bold=True
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Cycles the theme and returns to the menu.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            step = 1 if event.key == pygame.K_RIGHT else -1
            self.theme_index = (
                (self.theme_index + step) % len(AVAILABLE_THEMES)
            )
            new_theme = AVAILABLE_THEMES[self.theme_index]
            self.game.config.theme = new_theme

            if new_theme == "auto":
                self.game.theme_overridden = False
            else:
                self.game.theme_overridden = True

            # If inside an active run, synchronize immediately
            if hasattr(self.previous_scene, "game_scene"):
                g_scene = self.previous_scene.game_scene

                # If auto is chosen mid-game, resolve current level theme
                if new_theme == "auto":
                    progressive_list = AVAILABLE_THEMES[1:]
                    idx = (g_scene.engine.level - 1) // 2
                    idx = max(0, min(idx, len(progressive_list) - 1))
                    resolved_theme = progressive_list[idx]
                    g_scene.renderer.set_theme(resolved_theme)
                else:
                    g_scene.renderer.set_theme(new_theme)

        elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.game.change_scene(self.previous_scene)

    def update(self, dt: float) -> None:
        """No timed logic on the options screen.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass

    def draw(self, target: pygame.Surface) -> None:
        """Draws the heading, the theme selector, and the hints.

        Args:
            target: The arcade surface to draw onto.
        """
        # See if previous scene has a game_scene reference
        if (
            hasattr(self.previous_scene, "game_scene") and
            hasattr(self.previous_scene, "overlay")
        ):
            # Render the frozen underlying gameplay state frame
            self.previous_scene.game_scene.draw(target)
            # Re-use the existing pause translucent overlay surface layer
            target.blit(self.previous_scene.overlay, (0, 0))
        else:
            # Fall back to a solid black backdrop if opened from the main menu
            target.fill(BG_COLOR)

        title = self.title_font.render("OPTIONS", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(ARCADE_W // 2, 140))
        target.blit(title, title_rect)

        label = self.item_font.render("Theme", True, LABEL_COLOR)
        label_rect = label.get_rect(center=(ARCADE_W // 2, ARCADE_H // 2 - 40))
        target.blit(label, label_rect)

        theme_name = AVAILABLE_THEMES[self.theme_index]
        value = self.item_font.render(
            f"< {theme_name} >", True, VALUE_COLOR
        )
        value_rect = value.get_rect(
            center=(ARCADE_W // 2, ARCADE_H // 2 + 20)
        )
        target.blit(value, value_rect)

        hint = self.hint_font.render(
            "LEFT / RIGHT to change, ENTER to return", True, HINT_COLOR
        )
        hint_rect = hint.get_rect(center=(ARCADE_W // 2, ARCADE_H - 80))
        target.blit(hint, hint_rect)
