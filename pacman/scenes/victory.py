import pygame
from pacman.scenes.leaderboard_entry import LeaderboardEntryScene
from pacman.constants import ARCADE_W, ARCADE_H, BG_COLOR

TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
SUBTITLE_COLOR: tuple[int, int, int] = (0, 255, 0)
SCORE_COLOR: tuple[int, int, int] = (255, 255, 255)
NAME_COLOR: tuple[int, int, int] = (255, 255, 0)
HINT_COLOR: tuple[int, int, int] = (180, 180, 180)


class VictoryScene(LeaderboardEntryScene):
    """Victory screen shown after clearing the final level.

    Mirrors the game-over flow: shows the final score, lets the player
    type a name for the leaderboard, records it, and returns to the
    menu. The messaging celebrates the win rather than announcing a
    loss.
    """

    def draw(self, target: pygame.Surface) -> None:
        """Draws the heading, score, name field, and hint.

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
