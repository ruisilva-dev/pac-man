from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene

if TYPE_CHECKING:
    from pacman.game import Game

# Maximum characters allowed in a leaderboard name
MAX_NAME_LEN: int = 10


class LeaderboardEntryScene(Scene):
    """Base scene handling text input and high score submission.

    Provides the shared event loop for typing a name and submitting it
    to the leaderboard. Subclasses only need to provide the specific
    title, subtitle, and drawing implementation.

    Attributes:
        score: The final score achieved this run.
        name: The name being typed by the player.
        submitted: Whether the score has already been recorded.
        title_font: Font for the heading.
        info_font: Font for score and name.
        hint_font: Font for the hint line.
    """

    def __init__(self, game: "Game", score: int) -> None:
        """Initializes the text input buffer and standard fonts.

        Args:
            game: The coordinating Game instance.
            score: The final score from the finished run.
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

        self.game.audio.stop_music()

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

    def update(self, dt: float) -> None:
        """No timed logic on the game-over screen.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass
