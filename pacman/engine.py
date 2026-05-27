from mazegenerator import MazeGenerator


class PacmanEngine:
    """The core logic engine handling game mechanics and state records.

    This class provides a clean data interface contract that coordinates
    the grid matrix layout, running metrics, and player attributes
    independently of any active front-end graphical visualization loops.

    Attributes:
        config_path: The file system location of the game configuration.
        score: Aggregated game points earned by the player instance.
        lives: Remainder tracking tally for player survival attempts.
        grid: Two-dimensional matrix representing active map cell encodings.
    """

    def __init__(self, config_path: str) -> None:
        """Initializes a new game logic session with safe initial states.

        Args:
            config_path: The designated path to the source configuration asset.
        """
        self.config_path: str = config_path
        self.score: int = 0
        self.lives: int = 3

        generator: MazeGenerator = MazeGenerator(
            size=(15, 15),
            perfect=False,
            seed=42
        )

        self.grid: list[list[int]] = generator.maze
