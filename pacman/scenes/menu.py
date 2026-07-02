from typing import TYPE_CHECKING
import pygame
import os
from pacman.scenes.base import Scene
from pacman.constants import ARCADE_W, ARCADE_H, BG_COLOR

if TYPE_CHECKING:
    from pacman.game import Game

TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
ITEM_COLOR: tuple[int, int, int] = (255, 255, 255)
ITEM_SELECTED_COLOR: tuple[int, int, int] = (255, 255, 0)


class MenuScene(Scene):
    """Main menu with keyboard-navigable options.

    Attributes:
        options: Ordered labels shown in the menu.
        selected: Index of the currently highlighted option.
        title_font: Font for the game title.
        item_font: Font for the menu options.
    """

    def __init__(self, game: "Game") -> None:
        """Initializes the menu with its options and fonts.

        Args:
            game: The coordinating Game instance.
        """
        super().__init__(game)
        self.options: list[str] = [
            "Start Game", "High Scores", "Instructions", "Options", "Exit"
        ]
        self.selected: int = 0
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 72, bold=True
        )
        self.item_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 40, bold=True
        )
        banner_path = os.path.join("pacman", "assets",
                                   "textures", "banner.png")
        self.banner: pygame.Surface | None = None
        if os.path.exists(banner_path):
            self.banner = pygame.image.load(banner_path).convert_alpha()
        self.game.audio.play_music("menu_loop.wav", is_global=True)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Navigates the menu and activates the selected option.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.options)
            self.game.audio.play_sfx("menu_nav1.wav", is_global=True)
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.options)
            self.game.audio.play_sfx("menu_nav1.wav", is_global=True)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate()

    def _activate(self) -> None:
        """Performs the action for the highlighted option."""
        choice = self.options[self.selected]
        if choice == "Start Game":
            self.game.audio.stop_music()
            from pacman.scenes.game_scene import GameScene
            self.game.change_scene(GameScene(self.game))
        elif choice == "High Scores":
            from pacman.scenes.highscore import HighScoreScene
            self.game.change_scene(HighScoreScene(self.game))
        elif choice == "Instructions":
            from pacman.scenes.instructions import InstructionsScene
            self.game.change_scene(InstructionsScene(self.game, self))
        elif choice == "Options":
            from pacman.scenes.options import OptionsScene
            self.game.change_scene(OptionsScene(self.game, self))
        elif choice == "Exit":
            self.game.running = False
        self.game.audio.play_sfx("menu_confirm.wav", is_global=True)

    def update(self, dt: float) -> None:
        """No timed logic in the menu.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass

    def draw(self, target: pygame.Surface) -> None:
        """Draws the title and the menu options.

        Args:
            target: The arcade surface to draw onto.
        """
        target.fill(BG_COLOR)

        if self.banner is not None:
            banner_rect = self.banner.get_rect(
                center=(ARCADE_W // 2, ARCADE_H // 4)
            )
            target.blit(self.banner, banner_rect)
        else:
            title = self.title_font.render("PAC-MAN", True, TITLE_COLOR)
            title_rect = title.get_rect(center=(ARCADE_W // 2, ARCADE_H // 4))
            target.blit(title, title_rect)

        start_y: int = ARCADE_H // 2
        for i, option in enumerate(self.options):
            color = (
                ITEM_SELECTED_COLOR if i == self.selected else ITEM_COLOR
            )
            text = self.item_font.render(option, True, color)
            rect = text.get_rect(center=(ARCADE_W // 2, start_y + i * 70))
            target.blit(text, rect)

            # Selection marker to the left, without shifting the label.
            if i == self.selected:
                marker = self.item_font.render(">", True, color)
                marker_rect = marker.get_rect(
                    midright=(rect.left - 20, rect.centery)
                )
                target.blit(marker, marker_rect)
