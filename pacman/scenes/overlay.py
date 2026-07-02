from typing import TYPE_CHECKING
import pygame
from pacman.scenes.base import Scene
from pacman.constants import ARCADE_W, ARCADE_H, BG_COLOR

if TYPE_CHECKING:
    from pacman.game import Game


class OverlayScene(Scene):
    """Base class for pop-up menus that sit over a frozen background.

    Automatically captures the current state of the screen upon creation
    and applies a translucent dark overlay, eliminating the need to
    manually track and render previous scenes continuously.

    Attributes:
        previous_scene: The caller scene to return to upon exiting.
        background: A frozen snapshot of the screen with a dimming layer.
    """

    def __init__(self, game: "Game", previous_scene: Scene) -> None:
        """Captures the current arcade surface and applies a dim layer.

        Args:
            game: The coordinating Game instance.
            previous_scene: The scene that invoked this overlay.
        """
        super().__init__(game)
        self.previous_scene: Scene = previous_scene
        if isinstance(self.previous_scene, OverlayScene):
            self.background: pygame.Surface = self.previous_scene.background
        else:
            self.background = pygame.Surface(
                (ARCADE_W, ARCADE_H)
            )

        self.update_snapshot()

    def update_snapshot(self) -> None:
        """Captures the active gameplay frame and applies the dim layer."""
        # Local imports to prevent circular dependencies
        from pacman.scenes.game_scene import GameScene
        from pacman.scenes.pause import PauseScene

        # Resolve the active GameScene to get a clean background frame
        target_game_scene: GameScene | None = None

        if isinstance(self.previous_scene, GameScene):
            target_game_scene = self.previous_scene
        elif isinstance(self.previous_scene, PauseScene):
            target_game_scene = self.previous_scene.game_scene

        if target_game_scene:
            # Draw a frame of the game
            target_game_scene.draw(self.background)

            # Apply the translucent dimming overlay once
            dim_layer: pygame.Surface = pygame.Surface((ARCADE_W, ARCADE_H))
            dim_layer.fill((0, 0, 0))
            dim_layer.set_alpha(160)
            self.background.blit(dim_layer, (0, 0))
        else:
            # If opened from the main menu, use a solid background
            self.background.fill(BG_COLOR)

    def draw_background(self, target: pygame.Surface) -> None:
        """Blits the frozen, dimmed background onto the target surface.

        Subclasses should call this at the beginning of their draw method.

        Args:
            target: The arcade rendering surface layout canvas.
        """
        target.blit(self.background, (0, 0))
