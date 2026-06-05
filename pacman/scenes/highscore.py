from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.constants import ARCADE_W, ARCADE_H, BG_COLOR

if TYPE_CHECKING:
    from pacman.game import Game

TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
ENTRY_COLOR: tuple[int, int, int] = (255, 255, 255)
HINT_COLOR: tuple[int, int, int] = (180, 180, 180)


class HighScoreScene(Scene):
    """Displays the top-ten leaderboard read from the highscore manager.

    Attributes:
        game: Back-reference to the coordinating Game.
        title_font: Font for the heading.
        entry_font: Font for each score row.
        hint_font: Font for the return hint.
    """

    def __init__(self, game: "Game") -> None:
        """Loads the latest scores from disk for display.

        Args:
            game: The coordinating Game instance.
        """
        super().__init__(game)
        self.game.highscores.load_from_disk()
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 56, bold=True
        )
        self.entry_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 32, bold=True
        )
        self.hint_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 24, bold=True
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Returns to the menu on escape or enter.

        Args:
            event: The pygame event to handle.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                from pacman.scenes.menu import MenuScene
                self.game.change_scene(MenuScene(self.game))

    def update(self, dt: float) -> None:
        """No timed logic on the leaderboard.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass

    def draw(self, target: pygame.Surface) -> None:
        """Draws the heading, the score rows, and the return hint.

        Args:
            target: The arcade surface to draw onto.
        """
        target.fill(BG_COLOR)

        title = self.title_font.render("HIGH SCORES", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(ARCADE_W // 2, 120))
        target.blit(title, title_rect)

        scores = self.game.highscores.scores
        if not scores:
            empty = self.entry_font.render(
                "No scores yet", True, ENTRY_COLOR
            )
            empty_rect = empty.get_rect(center=(ARCADE_W // 2, ARCADE_H // 2))
            target.blit(empty, empty_rect)
        else:
            start_y: int = 240
            for i, entry in enumerate(scores):
                rank = f"{i + 1:2d}."
                name = str(entry["name"]).ljust(10)
                score = f"{int(entry['score']):06d}"
                line = f"{rank} {name} {score}"
                text = self.entry_font.render(line, True, ENTRY_COLOR)
                rect = text.get_rect(center=(ARCADE_W // 2, start_y + i * 48))
                target.blit(text, rect)

        hint = self.hint_font.render(
            "Press ENTER to return", True, HINT_COLOR
        )
        hint_rect = hint.get_rect(center=(ARCADE_W // 2, ARCADE_H - 80))
        target.blit(hint, hint_rect)
