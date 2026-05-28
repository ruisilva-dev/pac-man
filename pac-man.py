import sys
from pacman.config import Configuration
from pacman.engine import PacmanEngine
from pacman.game import Game


def main() -> None:
    """Main execution entry point for Pac-Man."""
    if len(sys.argv) < 2:
        sys.exit("Error: Please provide a config.json file.")

    # Instantiate our data container factory cleanly
    config: Configuration = Configuration.load(sys.argv[1])

    # Pass the clean configuration container to our engine
    engine: PacmanEngine = PacmanEngine(config)

    print("Engine Initialized Successfully!")
    print(f"Initial Score: {engine.score} | "
          f"Initial Lives: {engine.lives}")
    print("-" * 50)
    print("Launching graphical user interface layout view...")
    print("-" * 50)

    game: Game = Game(engine)
    game.run()


if __name__ == "__main__":
    main()
