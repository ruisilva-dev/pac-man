from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.engine import PacmanEngine
from pacman.render.renderer import GameRenderer
from pacman.constants import (
    ARCADE_W,
    ARCADE_H,
    HUD_BAR_H,
    BG_COLOR,
    AVAILABLE_THEMES,
    PAC_START_PAUSE,
    START_PAUSE_BY_THEME,
    CELL_SIZE
)

if TYPE_CHECKING:
    from pacman.game import Game


class GameScene(Scene):
    """The active gameplay scene.

    Owns the engine and the renderer. Drives the simulation, handles
    player input, composes the maze and HUD onto the arcade surface, and
    transitions to the game-over scene when the player runs out of
    lives.

    Attributes:
        engine: The gameplay logic engine for this run.
        renderer: Draws the maze, actors, and HUD.
        _death_started: Internal flag tracking if the death animation
            has begun.
        _stage_cleared: Status flag signaling the current level is clear.
        last_dt: Delta time from the latest update, reused when drawing
            so animations advance once per frame.
    """

    def __init__(self, game: "Game") -> None:
        """Creates a fresh engine and renderer for a new run.

        Args:
            game: The coordinating Game instance.
        """
        super().__init__(game)
        self.engine: PacmanEngine = PacmanEngine(game.config)

        # Auto theme progression
        self.initial_theme = game.config.theme
        if self.initial_theme == "auto":
            self.initial_theme = "classic"  # Level 1 always starts on classic
            game.audio.set_theme(self.initial_theme)
        else:
            game.audio.set_theme(self.initial_theme)
        self.current_theme = self.initial_theme
        self.audio_theme = self.initial_theme
        self.game.audio.play_music("song.wav", fallback="song.wav")

        self.renderer: GameRenderer = GameRenderer(
            self.engine, game.loader, theme=self.initial_theme
        )
        self._death_started: bool = False
        self._stage_cleared: bool = False
        self.last_dt: float = 0.0
        self._last_score: int = 0
        self.ready_font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 34, bold=True
        )
        self.engine.respawn_pause_timer = START_PAUSE_BY_THEME.get(
            self.current_theme, PAC_START_PAUSE
        )

    def _advance_stage(self) -> None:
        """Handles stage completion progression and automated theme swaps."""
        if self.engine.level >= 10:
            from pacman.scenes.victory import VictoryScene
            self.game.change_scene(VictoryScene(self.game, self.engine.score))
            self.game.audio.play_music("victory.wav", loops=0, is_global=True)

        else:
            self.engine.advance_level()

            # Automatic transition triggers only if no user override exists
            if not self.game.theme_overridden:
                progressive_themes = AVAILABLE_THEMES[1:]

                # Math indexes safely across available themes
                theme_idx = (self.engine.level - 1) // 2
                theme_idx = max(0, min(theme_idx, len(progressive_themes) - 1))
                target_theme = progressive_themes[theme_idx]

                self.game.audio.set_theme(target_theme)
                self.game.audio.stop_music()
                self.game.audio.play_music("song.wav", fallback="song.wav")
                self.renderer.set_theme(target_theme)
                self.current_theme = target_theme
            else:
                # Retain manual layout selection across level transitions
                self.renderer.set_theme(self.game.config.theme)
                self.current_theme = self.game.config.theme

                # Updates AudioManager to the manually chosen theme
                self.game.audio.set_theme(self.current_theme)
                # Forces Music to stop
                self.game.audio.stop_music()
                # Starts playing theme song for the level
                self.game.audio.play_music("song.wav", fallback="song.wav")

            self.engine.respawn_pause_timer = START_PAUSE_BY_THEME.get(
                self.current_theme, PAC_START_PAUSE
            )

    def sync_theme(self) -> None:
        """Resolves active configuration theme, updates audio and graphics."""
        target_theme = self.game.config.theme

        if target_theme == "auto":
            progressive_themes = AVAILABLE_THEMES[1:]
            theme_idx = (self.engine.level - 1) // 2
            theme_idx = max(0, min(theme_idx, len(progressive_themes) - 1))
            target_theme = progressive_themes[theme_idx]

        self.game.audio.set_theme(target_theme)
        self.renderer.set_theme(target_theme)
        self.current_theme = target_theme

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handles movement keys, pausing, cheats and level advancement.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        # If stage is cleared, ignore all gameplay inputs except ENTER
        if self._stage_cleared:
            if event.key == pygame.K_RETURN:
                self._stage_cleared = False
                self._advance_stage()
            return

        if event.key == pygame.K_RIGHT:
            self.engine.player.buffer_input('E')
        elif event.key == pygame.K_LEFT:
            self.engine.player.buffer_input('W')
        elif event.key == pygame.K_UP:
            self.engine.player.buffer_input('N')
        elif event.key == pygame.K_DOWN:
            self.engine.player.buffer_input('S')
        elif event.key == pygame.K_ESCAPE:
            from pacman.scenes.pause import PauseScene
            self.game.change_scene(PauseScene(self.game, self))

        # Cheats
        elif event.key == pygame.K_F1:
            self.engine.cheat_freeze = not self.engine.cheat_freeze
        elif event.key == pygame.K_F2:
            self._advance_stage()
        elif event.key == pygame.K_F3:
            self.engine.cheat_invincible = not self.engine.cheat_invincible
        elif event.key == pygame.K_F4:
            self.engine.lives = min(5, self.engine.lives + 1)
        elif event.key == pygame.K_F5:
            self.engine.cheat_speed = not self.engine.cheat_speed

    def update(self, dt: float) -> None:
        """Advances the simulation and checks for game over or stage clears.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        # If visual theme is different from the audio theme that was playing
        if self.current_theme != self.audio_theme:
            self.game.audio.stop_music()
            self.game.audio.play_music("song.wav", fallback="song.wav")
            self.audio_theme = self.current_theme  # Atualiza o rastreador

            # Resets the freeze timer if its still in the round start
            if self.engine.respawn_pause_timer > 0.0:
                self.engine.respawn_pause_timer = START_PAUSE_BY_THEME.get(
                    self.current_theme, PAC_START_PAUSE
                )
        self.last_dt = dt

        # Freeze updates if waiting for user confirmation
        if self._stage_cleared:
            return

        if self.engine.player.is_dying:
            if not self._death_started:
                self.renderer.start_death()
                self._death_started = True
                self.game.audio.stop_frightened_sound()
                self.game.audio.play_sfx("death.wav", is_global=True)
        else:
            self._death_started = False
            self.engine.update(dt)

            if self.engine.score > self._last_score:
                self.game.audio.play_sfx("eat.wav", is_global=True)
            self._last_score = self.engine.score

            any_frightened = any(
                ghost.state == "FRIGHTENED" for ghost in self.engine.ghosts
            )
            if any_frightened:
                self.game.audio.start_frightened_sound()
            else:
                self.game.audio.stop_frightened_sound()

            if not self.engine.has_items():
                self.game.audio.play_music("stage_clear.wav", loops=0,
                                           is_global=True)
                self._stage_cleared = True

        # Out of lives -> record score and go to game over.
        if self.engine.lives <= 0:
            from pacman.scenes.game_over import GameOverScene
            self.game.change_scene(
                GameOverScene(self.game, self.engine.score)
            )
            self.game.audio.play_music("game_over.wav", loops=0,
                                       is_global=True)

    def draw(self, target: pygame.Surface) -> None:
        """Composes the maze and HUD onto the arcade surface.

        Args:
            target: The arcade surface to draw onto.
        """
        dt = self.last_dt
        self.last_dt = 0.0

        self.renderer.draw_grid()
        if self.engine.player.is_dying:
            self.renderer.draw_items(0.0)
            self.renderer.draw_ghosts(0.0)
            self.renderer.draw_death(dt)
        else:
            self.renderer.draw_items(dt)
            self.renderer.draw_ghosts(dt)
            self.renderer.draw_pacman(dt)

        # Compose: HUD bars + centered world.
        target.fill(BG_COLOR)
        world = self.renderer.world_surface
        play_h: int = ARCADE_H - HUD_BAR_H * 2
        x: int = (ARCADE_W - world.get_width()) // 2
        y: int = HUD_BAR_H + (play_h - world.get_height()) // 2
        target.blit(world, (x, y))
        self.renderer.draw_hud(target, self.game.highscores.best())

        if self.engine.respawn_pause_timer > 0.0 and not self._stage_cleared:
            if self.current_theme in ("hawaii", "worldcup"):
                ready_color = (0, 0, 0)
            else:
                ready_color = (255, 255, 0)
            get_surf = self.ready_font.render("GET", True, ready_color)
            ready_surf = self.ready_font.render("READY", True, ready_color)

            get_rect = get_surf.get_rect(
                center=(ARCADE_W // 2 - (CELL_SIZE * 2), ARCADE_H // 2)
            )
            ready_rect = ready_surf.get_rect(
                center=(ARCADE_W // 2 + (CELL_SIZE * 2), ARCADE_H // 2)
            )

            target.blit(get_surf, get_rect)
            target.blit(ready_surf, ready_rect)

        # Render the Stage Clear overlay prompt if active
        if self._stage_cleared:
            # Overlay block
            overlay = pygame.Surface((ARCADE_W, ARCADE_H))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            target.blit(overlay, (0, 0))

            # Announcement text surfaces
            font_big = pygame.font.SysFont("monospace", 48, bold=True)
            font_sm = pygame.font.SysFont("monospace", 24, bold=True)

            clear_surf = font_big.render("LEVEL CLEARED!", True, (0, 255, 0))
            prompt_surf = font_sm.render(
                "PRESS ENTER TO CONTINUE", True, (255, 255, 255)
            )

            c_rect = clear_surf.get_rect(
                center=(ARCADE_W // 2, ARCADE_H // 2 - 30)
            )
            p_rect = prompt_surf.get_rect(
                center=(ARCADE_W // 2, ARCADE_H // 2 + 30)
            )

            target.blit(clear_surf, c_rect)
            target.blit(prompt_surf, p_rect)
