import sys
from pacman.engine import PacmanEngine


def main() -> None:
    """Main execution entry point for Pac-Man."""
    if len(sys.argv) < 2:
        sys.exit("Error: Please provide a config.json file.")

    # Instantiate the backend simulation engine using the user's config file
    engine: PacmanEngine = PacmanEngine(sys.argv[1])

    print("Engine Initialized Successfully!")
    print(f"Initial Score: {engine.score} | Initial Lives: {engine.lives}")
    print("-" * 50)
    print("Displaying Level 1 Grid Bitwise Encodings:")
    print("-" * 50)

    # Iterative test printer for the map layout
    for row in engine.grid:
        # Align integers cleanly so columns match symmetrically in the console
        print(" ".join(f"{cell:2d}" for cell in row))


if __name__ == "__main__":
    main()
