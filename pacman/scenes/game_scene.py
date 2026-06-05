from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.engine import PacmanEngine
from pacman.render.renderer import GameRenderer
from pacman.constants import ARCADE_W, ARCADE_H, HUD_BAR_H, BG_COLOR

if TYPE_CHECKING:
    from pacman.game import Game


class GameScene(Scene):
    """The active gameplay scene.

    Owns the engine and the renderer. Drives the simulation, handles
    player input, composes the maze and HUD onto the arcade surface, and
    transitions to the game-over scene when the player runs out of
    lives.

    Attributes:
        game: Back-reference to the coordinating Game.
        engine: The gameplay logic engine for this run.
        renderer: Draws the maze, actors, and HUD.
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
        self.renderer: GameRenderer = GameRenderer(
            self.engine, game.loader, theme=game.config.theme
        )
        self._death_started: bool = False
        self.last_dt: float = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handles movement keys and pausing.

        Args:
            event: The pygame event to handle.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RIGHT:
            self.engine.pac_next_dir = 'E'
            self.engine.pac_next_dir_timer = 0.0
        elif event.key == pygame.K_LEFT:
            self.engine.pac_next_dir = 'W'
            self.engine.pac_next_dir_timer = 0.0
        elif event.key == pygame.K_UP:
            self.engine.pac_next_dir = 'N'
            self.engine.pac_next_dir_timer = 0.0
        elif event.key == pygame.K_DOWN:
            self.engine.pac_next_dir = 'S'
            self.engine.pac_next_dir_timer = 0.0
        elif event.key == pygame.K_ESCAPE:
            from pacman.scenes.pause import PauseScene
            self.game.change_scene(PauseScene(self.game, self))

    def update(self, dt: float) -> None:
        """Advances the simulation and checks for game over.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        self.last_dt = dt

        if self.engine.pac_dying:
            if not self._death_started:
                self.renderer.start_death()
                self._death_started = True
        else:
            self._death_started = False
            self.engine.update(dt)

        # Out of lives -> record score and go to game over.
        if self.engine.lives <= 0:
            from pacman.scenes.game_over import GameOverScene
            self.game.change_scene(
                GameOverScene(self.game, self.engine.score)
            )

    def draw(self, target: pygame.Surface) -> None:
        """Composes the maze and HUD onto the arcade surface.

        Args:
            target: The arcade surface to draw onto.
        """
        dt = self.last_dt

        self.renderer.draw_grid()
        if self.engine.pac_dying:
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
