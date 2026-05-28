import sys
from pacman.engine import PacmanEngine
from pacman.game import Game


def main() -> None:
    """Main execution entry point for Pac-Man."""
    if len(sys.argv) < 2:
        sys.exit("Error: Please provide a config.json file.")

    engine: PacmanEngine = PacmanEngine(sys.argv[1])

    print("Engine Initialized Successfully!")
    print(f"Initial Score: {engine.score} | Initial Lives: {engine.lives}")
    print("-" * 50)
    print("Launching graphical game user interface window view...")
    print("-" * 50)

    game: Game = Game(engine)
    game.run()


if __name__ == "__main__":
    main()
