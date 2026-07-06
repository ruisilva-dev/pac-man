import sys
import os
from pacman.config import Configuration
from pacman.game import Game


def main() -> None:
    """Main execution entry point for Pac-Man."""
    # Determine base path for application
    base_path = os.path.abspath(os.path.dirname(__file__))

    # Argument enforcement
    if len(sys.argv) > 1:
        config_path = os.path.abspath(sys.argv[1])
    else:
        # If running from source, strictly demand the argument
        if not getattr(sys, 'frozen', False):
            print("Usage: python3 pac-man.py config.json")
            sys.exit(1)
        # If running a binary file, allow double-click execution to use default
        exe_folder = os.path.dirname(sys.executable)
        config_path = os.path.join(exe_folder, "config.json")

    config: Configuration = Configuration.load(config_path)

    game: Game = Game(config, config_path, base_path)
    game.run()


if __name__ == "__main__":
    main()
