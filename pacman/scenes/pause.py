from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.constants import ARCADE_W, ARCADE_H
from pacman.scenes.game_scene import GameScene

if TYPE_CHECKING:
    from pacman.game import Game

OVERLAY_COLOR: tuple[int, int, int] = (0, 0, 0)
OVERLAY_ALPHA: int = 160
TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
ITEM_COLOR: tuple[int, int, int] = (255, 255, 255)
ITEM_SELECTED_COLOR: tuple[int, int, int] = (255, 255, 0)


class PauseScene(Scene):
    """Pause overlay drawn on top of a frozen gameplay scene.

    Holds the GameScene it suspended so it can render that scene's last
    frame underneath a translucent dimming layer, with a small menu to
    either resume or quit back to the main menu.

    Attributes:
        game: Back-reference to the coordinating Game.
        game_scene: The suspended gameplay scene shown underneath.
        options: The pause menu options.
        selected: Index of the highlighted option.
        title_font: Font for the PAUSED label.
        item_font: Font for the options.
        overlay: Pre-built translucent dimming surface.
    """

    def __init__(self, game: "Game", game_scene: GameScene) -> None:
        """Captures the gameplay scene to overlay.

        Args:
            game: The coordinating Game instance.
            game_scene: The gameplay scene being paused.
        """
        super().__init__(game)
        self.game_scene: GameScene = game_scene
        self.options: list[str] = [
            "Resume", "Restart Game", "Instructions", "Options", "Quit to Menu"
        ]
        self.selected: int = 0
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 64, bold=True
        )
        self.item_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 36, bold=True
        )
        self.overlay: pygame.Surface = pygame.Surface((ARCADE_W, ARCADE_H))
        self.overlay.fill(OVERLAY_COLOR)
        self.overlay.set_alpha(OVERLAY_ALPHA)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Navigates the pause menu and activates the choice.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            # Escape is a shortcut to resume.
            self.game.change_scene(self.game_scene)
        elif event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.options)
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate()

    def _activate(self) -> None:
        """Performs the highlighted pause action."""
        if self.options[self.selected] == "Resume":
            self.game.change_scene(self.game_scene)
        elif self.options[self.selected] == "Restart Game":
            engine = self.game_scene.engine

            engine.level = 1
            engine.score = 0
            engine.lives = self.game.config.lives
            engine.level_timer = 90.0

            engine._build_level(seed=self.game.config.seed)
            self.game_scene.renderer.set_theme(self.game.config.theme)
            self.game.change_scene(self.game_scene)
        elif self.options[self.selected] == "Instructions":
            from pacman.scenes.instructions import InstructionsScene
            self.game.change_scene(InstructionsScene(self.game, self))
        elif self.options[self.selected] == "Options":
            from pacman.scenes.options import OptionsScene
            self.game.change_scene(OptionsScene(self.game, self))
        else:
            from pacman.scenes.menu import MenuScene
            self.game.change_scene(MenuScene(self.game))

    def update(self, dt: float) -> None:
        """Does nothing; gameplay is frozen while paused.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass

    def draw(self, target: pygame.Surface) -> None:
        """Draws the frozen game, the dim overlay, and the menu.

        Args:
            target: The arcade surface to draw onto.
        """
        self.game_scene.draw(target)
        target.blit(self.overlay, (0, 0))

        title = self.title_font.render("PAUSED", True, TITLE_COLOR)
        title_rect = title.get_rect(
            center=(ARCADE_W // 2, ARCADE_H // 2 - 100)
        )
        target.blit(title, title_rect)

        for i, option in enumerate(self.options):
            color = (
                ITEM_SELECTED_COLOR if i == self.selected else ITEM_COLOR
            )
            text = self.item_font.render(option, True, color)
            rect = text.get_rect(
                center=(ARCADE_W // 2, ARCADE_H // 2 + i * 60)
            )
            target.blit(text, rect)
            if i == self.selected:
                marker = self.item_font.render(">", True, color)
                marker_rect = marker.get_rect(
                    midright=(rect.left - 20, rect.centery)
                )
                target.blit(marker, marker_rect)
