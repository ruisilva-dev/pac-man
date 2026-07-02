from pacman.scenes.base import Scene
from pacman.scenes.overlay import OverlayScene
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pacman.game import Game
from pacman.constants import ARCADE_W, ARCADE_H
import pygame


class InstructionsScene(OverlayScene):
    """Displays movement keys, cheat hotkeys, and game mechanics rules.

    Attributes:
        title_font: Font used for the main screen heading.
        info_font: Font used for the instruction list and descriptions.
        hint_font: Font used for the bottom navigation hints.
    """

    TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)  # Yellow

    def __init__(self, game: "Game", previous_scene: Scene) -> None:
        super().__init__(game, previous_scene)

        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 56, bold=True
        )
        self.info_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 36, bold=True
        )
        self.hint_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 24, bold=True
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Returns to the caller scene when a navigation key is hit."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.game.change_scene(self.previous_scene)

    def update(self, dt: float) -> None:
        """No timed animation logic or physics updates occur on this layer.

        Args:
            dt: Delta time tracking in seconds since last frame pass.
        """
        pass

    def draw(self, target: pygame.Surface) -> None:
        """Draws clean text line blocks mapping input keys and cheat utilities.

        Args:
            target: The arcade rendering surface layout coordinate canvas.
        """
        self.draw_background(target)

        # Draw Title
        title = self.title_font.render("INSTRUCTIONS", True, (255, 255, 0))
        title_rect = title.get_rect(center=(ARCADE_W // 2, 120))
        target.blit(title, title_rect)

        # Instructions
        lines: list[str] = [
            "ARROWS : Move Pac-Man",
            "ESC : Pause Gameplay",
            "F1 : Freeze All Ghosts",
            "F2 : Instantly Skip Current Level",
            "F3 : Toggle Invincibility",
            "F4 : Increment +1 Extra Life",
            "F5 : Double Movement Speed",
        ]

        start_y: int = ARCADE_H // 2 - 150
        line_height: int = 50

        for i, text_string in enumerate(lines):
            if " : " in text_string:
                key_part, desc_part = text_string.split(" : ", 1)

                # Render key label
                k_surf = self.info_font.render(key_part, True, (255, 255, 0))
                # Render separator and description
                d_surf = self.info_font.render(
                    f": {desc_part}", True, (255, 255, 255)
                )

                # Align
                total_w = k_surf.get_width() + d_surf.get_width()
                row_x = (ARCADE_W - total_w) // 2
                row_y = start_y + (i * line_height)

                target.blit(k_surf, (row_x, row_y))
                target.blit(d_surf, (row_x + k_surf.get_width(), row_y))

        # Footer
        hint = self.hint_font.render(
            "Press ESC or ENTER to return", True, (180, 180, 180)
        )
        hint_rect = hint.get_rect(center=(ARCADE_W // 2, ARCADE_H - 80))
        target.blit(hint, hint_rect)
