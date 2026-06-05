import sys
from pacman.config import Configuration
from pacman.game import Game


def main() -> None:
    """Main execution entry point for Pac-Man."""
    if len(sys.argv) < 2:
        print("Usage: python3 pac-man.py config.json")
        sys.exit(1)

    config_path: str = sys.argv[1]
    config: Configuration = Configuration.load(config_path)

    game: Game = Game(config, config_path)
    game.run()


if __name__ == "__main__":
    main()
