from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from pacman.engine import PacmanEngine


class Consumable(ABC):
    """Abstract base class representing an in-game collectible entity.

    Attributes:
        points: The score point payload awarded upon item consumption.
    """

    def __init__(self, points: int) -> None:
        """Initializes a consumable item instance with a point value.

        Args:
            points: Score point reward yield.
        """
        self.points: int = points

    @abstractmethod
    def on_consume(self, engine: "PacmanEngine") -> None:
        """Abstract handler executed when Pac-Man consumes the item.

        Args:
            engine: Shared reference to the central game logic driver.
        """
        ...


class Pacgum(Consumable):
    """A standard pacgum item pellet that awards score points."""

    def on_consume(self, engine: "PacmanEngine") -> None:
        """Increments the game score value by the item's points payload.

        Args:
            engine: Shared reference to the central game logic driver.
        """
        engine.score += self.points


class SuperPacgum(Pacgum):
    """A large power pellet that awards points and alters ghost states."""

    def on_consume(self, engine: "PacmanEngine") -> None:
        """Triggers base point rewards and activates ghost vulnerability.

        Args:
            engine: Shared reference to the central game logic driver.
        """
        super().on_consume(engine)
        engine.activate_frightened_mode()
