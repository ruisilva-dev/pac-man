from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.scenes.overlay import OverlayScene
from pacman.scenes.pause import PauseScene
from pacman.constants import ARCADE_W, ARCADE_H, AVAILABLE_THEMES

if TYPE_CHECKING:
    from pacman.game import Game

TITLE_COLOR: tuple[int, int, int] = (255, 255, 0)
LABEL_COLOR: tuple[int, int, int] = (255, 255, 255)
VALUE_COLOR: tuple[int, int, int] = (255, 255, 0)
HINT_COLOR: tuple[int, int, int] = (180, 180, 180)


class OptionsScene(OverlayScene):
    """Lets the player cycle the active theme and adjust volumes.

    Changing the theme updates the shared configuration so subsequent
    gameplay scenes load the chosen theme. Volume changes are applied
    instantly to the AudioManager.

    Attributes:
        theme_index: Index into AVAILABLE_THEMES for the current theme.
        selected: Tracks which menu option is focused.
        options: List of available settings to change.
        title_font: Font for the heading.
        item_font: Font for the option rows.
        hint_font: Font for the navigation hint.
    """

    def __init__(self, game: "Game", previous_scene: Scene) -> None:
        """Initializes the options screen at the current theme.

        Args:
            game: The coordinating Game instance.
            previous_scene: Scene to return to (Menu or Pause).
        """
        super().__init__(game, previous_scene)
        current = game.config.theme
        self.theme_index: int = (
            AVAILABLE_THEMES.index(current)
            if current in AVAILABLE_THEMES else 0
        )
        # 0 = Theme, 1 = Music Volume, 2 = SFX Volume
        self.options: list[str] = ["Theme", "Music Volume", "SFX Volume"]
        self.selected: int = 0
        self.title_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 56, bold=True
        )
        self.item_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 36, bold=True
        )
        self.hint_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 24, bold=True
        )

    def _get_volume_bar(self, volume: float) -> str:
        """Converts a float volume (0.0 to 1.0) into a visual text bar."""
        filled = int(round(volume * 10))
        empty = 10 - filled
        return f"< {'|' * filled}{'.' * empty} >"

    def handle_event(self, event: pygame.event.Event) -> None:
        """Cycles the theme, adjusts volumes, and returns to the menu.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        # VERTICAL NAV
        if event.key in (pygame.K_UP, pygame.K_DOWN):
            self.game.audio.play_sfx("menu_nav1.wav", is_global=True)
            step = 1 if event.key == pygame.K_DOWN else -1
            self.selected = (self.selected + step) % len(self.options)

        # HORIZONTAL NAV
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.game.audio.play_sfx("menu_nav1.wav", is_global=True)
            step = 1 if event.key == pygame.K_RIGHT else -1

            # OPTION 0: THEME
            if self.selected == 0:
                self.theme_index = ((self.theme_index + step)
                                    % len(AVAILABLE_THEMES))
                new_theme = AVAILABLE_THEMES[self.theme_index]
                self.game.config.theme = new_theme
                self.game.theme_overridden = new_theme != "auto"

                # If inside an active run, synchronize immediately
                if isinstance(self.previous_scene, PauseScene):
                    g_scene = self.previous_scene.game_scene
                    g_scene.sync_theme()
                    self.update_snapshot()  # We only snapshot if theme changes

            # OPTION 1: MUSIC VOLUME
            elif self.selected == 1:
                # Rounding avoids python bugs (ex: 0.300000004)
                new_vol = round(self.game.audio.music_volume + (step * 0.1), 1)
                self.game.audio.music_volume = max(0.0, min(1.0, new_vol))
                pygame.mixer.music.set_volume(self.game.audio.music_volume)

            # OPTION 2: SFX VOLUME
            elif self.selected == 2:
                new_vol = round(self.game.audio.sfx_volume + (step * 0.1), 1)
                self.game.audio.sfx_volume = max(0.0, min(1.0, new_vol))
                # Toca o som do pacman a comer para dar feedback do novo volume
                self.game.audio.play_sfx("eat.wav", is_global=True)

        # RETURN (ESC ou ENTER)
        elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.game.audio.play_sfx("menu_confirm.wav", is_global=True)
            self.game.change_scene(self.previous_scene)

    def update(self, dt: float) -> None:
        """No timed logic on the options screen."""
        pass

    def draw(self, target: pygame.Surface) -> None:
        """Draws the heading, the options, and the hints."""
        self.draw_background(target)

        title = self.title_font.render("OPTIONS", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(ARCADE_W // 2, 120))
        target.blit(title, title_rect)

        # Initial position of the options list
        start_y = ARCADE_H // 2 - 120

        for i, option_name in enumerate(self.options):
            # Color change to yellow if selected
            color = VALUE_COLOR if i == self.selected else LABEL_COLOR

            # 1. Draws the labels ("Theme", "Music Volume", "SFX")
            label = self.item_font.render(option_name, True, LABEL_COLOR)
            label_rect = label.get_rect(center=(ARCADE_W // 2,
                                                start_y + i * 110))
            target.blit(label, label_rect)

            # 2. Finds which value to show
            if i == 0:
                val_str = f"< {AVAILABLE_THEMES[self.theme_index]} >"
            elif i == 1:
                val_str = self._get_volume_bar(self.game.audio.music_volume)
            else:
                val_str = self._get_volume_bar(self.game.audio.sfx_volume)
            # 3. Drawing the value under the label
            value = self.item_font.render(val_str, True, color)
            value_rect = value.get_rect(center=(ARCADE_W // 2,
                                                start_y + i * 110 + 35))
            target.blit(value, value_rect)

        hint = self.hint_font.render(
            "UP/DOWN select, L/R change, ENTER return", True, HINT_COLOR
        )
        hint_rect = hint.get_rect(center=(ARCADE_W // 2, ARCADE_H - 80))
        target.blit(hint, hint_rect)
