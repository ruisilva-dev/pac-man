from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.constants import ARCADE_W, ARCADE_H, BG_COLOR

if TYPE_CHECKING:
    from pacman.game import Game


TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
SUBTITLE_COLOR: tuple[int, int, int] = (0, 255, 0)
SCORE_COLOR: tuple[int, int, int] = (255, 255, 255)
NAME_COLOR: tuple[int, int, int] = (255, 255, 0)
HINT_COLOR: tuple[int, int, int] = (180, 180, 180)
MAX_NAME_LEN: int = 10


class VictoryScene(Scene):
    """Victory screen shown after clearing the final level.

    Mirrors the game-over flow: shows the final score, lets the player
    type a name for the leaderboard, records it, and returns to the
    menu. The messaging celebrates the win rather than announcing a
    loss.

    Attributes:
        game: Back-reference to the coordinating Game.
        score: The final score achieved across the full run.
        name: The name being typed by the player.
        submitted: Whether the score has already been recorded.
        title_font: Font for the heading.
        info_font: Font for score and name.
        hint_font: Font for the hint line.
    """
    def __init__(self, game: "Game", score: int) -> None:
        """
        Initializes the victory screen with the final score.
        Args:
            game: The coordinating Game instance.
            score: The final score from the completed run.
        """
        super().__init__(game)
        self.score: int = score
        self.name: str = ""
        self.submitted: bool = False
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 64, bold=True
        )
        self.info_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 36, bold=True
        )
        self.hint_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 24, bold=True
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Captures typed characters and confirms the entry.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            from pacman.scenes.menu import MenuScene
            self.game.change_scene(MenuScene(self.game))
        elif event.key == pygame.K_RETURN:
            self._submit()
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif event.unicode.isprintable() and len(self.name) < MAX_NAME_LEN:
            self.name += event.unicode

    def _submit(self) -> None:
        """Records the score under the typed name and returns to menu."""
        if self.submitted:
            return
        name = self.name.strip() or "Unknown"
        self.game.highscores.add_score(name, self.score)
        self.game.highscores.save_to_disk()
        self.submitted = True
        from pacman.scenes.menu import MenuScene
        self.game.change_scene(MenuScene(self.game))

    def update(self, dt: float) -> None:
        """
        No timed logic on the victory screen.
        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass

    def draw(self, target: pygame.Surface) -> None:
        """
        Draws the heading, score, name field, and hint.

        Args:
            target: The arcade surface to draw onto.
        """
        target.fill(BG_COLOR)
        title = self.title_font.render("YOU WIN", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(ARCADE_W // 2, ARCADE_H // 4))
        target.blit(title, title_rect)

        subtitle = self.info_font.render(
            "ALL LEVELS CLEARED", True, SUBTITLE_COLOR
        )
        subtitle_rect = subtitle.get_rect(
            center=(ARCADE_W // 2, ARCADE_H // 4 + 60)
        )
        target.blit(subtitle, subtitle_rect)
        score_text = self.info_font.render(
            f"SCORE  {self.score:06d}", True, SCORE_COLOR
        )
        score_rect = score_text.get_rect(
            center=(ARCADE_W // 2, ARCADE_H // 2 - 40)
        )
        target.blit(score_text, score_rect)

        prompt = self.info_font.render("ENTER YOUR NAME", True, SCORE_COLOR)
        prompt_rect = prompt.get_rect(
            center=(ARCADE_W // 2, ARCADE_H // 2 + 30)
        )
        target.blit(prompt, prompt_rect)

        # Name field with a trailing underscore cursor.
        shown = self.name + "_"
        name_text = self.info_font.render(shown, True, NAME_COLOR)
        name_rect = name_text.get_rect(
            center=(ARCADE_W // 2, ARCADE_H // 2 + 90)
        )
        target.blit(name_text, name_rect)

        hint = self.hint_font.render(
            "Type a name, then press ENTER to submit or ESC to return to Menu",
            True,
            HINT_COLOR
        )
        hint_rect = hint.get_rect(center=(ARCADE_W // 2, ARCADE_H - 80))
        target.blit(hint, hint_rect)
