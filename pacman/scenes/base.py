from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from pacman.game import Game


class Scene(ABC):
    """Abstract base for every screen in the game.

    A scene owns its own input handling, update logic, and drawing. The
    Game holds exactly one active scene at a time and delegates the loop
    to it. Scenes draw onto the shared arcade surface; the Game performs
    the final scaling to the window once, for whichever scene is active.

    Attributes:
        game: Back-reference to the coordinating Game, used to request
            scene transitions and to reach shared resources (loader,
            arcade surface, configuration).
    """

    def __init__(self, game: "Game") -> None:
        """Binds the scene to its coordinating Game.

        Args:
            game: The Game instance that owns and drives this scene.
        """
        self.game: "Game" = game

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes a single input event.

        Args:
            event: The pygame event to handle.
        """
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advances the scene's logic by one frame.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        ...

    @abstractmethod
    def draw(self, target: pygame.Surface) -> None:
        """Draws the scene onto the target surface.

        Args:
            target: The arcade surface to draw onto.
        """
        ...

    def on_exit(self) -> None:
        """Called when this scene is replaced. Override to clean up."""
        self.game.audio.stop_all_sfx()
