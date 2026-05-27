import sys


def main() -> None:
    """Main execution entry point for Pac-Man."""
    if len(sys.argv) < 2:
        sys.exit("Error: Please provide a config.json file.")

    print(f"Hello from pac-man! Config file: {sys.argv[1]}")


if __name__ == "__main__":
    main()
