import sys
from pacman.config import Configuration
from pacman.engine import PacmanEngine
from pacman.game import Game
from pacman.highscores import HighscoreManager


def main() -> None:
    """Main execution entry point for Pac-Man."""
    if len(sys.argv) < 2:
        print("Usage: python3 pac-man.py config.json")
        sys.exit(1)

    config_path: str = sys.argv[1]

    # Instantiate our data container factory cleanly
    config: Configuration = Configuration.load(config_path)

    # Initialize and boot highscores at game start
    highscore_mgr = HighscoreManager(config.highscore_filename, config_path)
    highscore_mgr.load_from_disk()

    # Pass the clean configuration container to our engine
    engine: PacmanEngine = PacmanEngine(config)

    print("Engine Initialized Successfully!")
    print(f"Initial Score: {engine.score} | "
          f"Initial Lives: {engine.lives} | "
          f"Highscore File: {highscore_mgr.filename}")
    print("-" * 50)
    print("Launching graphical user interface layout view...")
    print("-" * 50)

    game: Game = Game(engine)
    game.run()


if __name__ == "__main__":
    main()
