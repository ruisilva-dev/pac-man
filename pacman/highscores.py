import os
import sys
import json


class HighscoreManager:
    """Manages loading, validation, and persistence of player scores.

    Attributes:
        filename: Cleaned and validated target storage path for scores.
        scores: Collection of sanitized top 10 player score records.
    """

    def __init__(self, filename: str, config_path: str) -> None:
        """Initializes highscore manager with a safe file destination.

        Args:
            filename: Proposed path or name for the highscore file.
            config_path: Path to the active game configuration.
        """
        self.filename: str = self._sanitize_path(filename, config_path)
        self.scores: list[dict[str, str | int]] = []

    def _sanitize_path(self, target_path: str, config_path: str) -> str:
        """Sanitizes highscore path against system vulnerabilities.

        Ensures the highscore file has a .json extension, doesn't collide
        with the config file, and does not pollute source folders.

        Args:
            target_path: Proposed destination path for the highscore file.
            config_path: File path used to launch the active game loop.

        Returns:
            A safe, validated file path string for disk operations.
        """
        default = "highscores.json"
        if os.path.abspath(default) == os.path.abspath(config_path):
            default = "backup_highscores.json"

        base_name = os.path.basename(target_path).strip()

        # Prevent empty string / folder only path
        if not base_name:
            print("Warning: Highscore filename is empty. Using default.")
            return default

        # Enforce json extension
        if not base_name.endswith(".json"):
            print(
                f"Warning: Highscore file '{base_name}' must be JSON. "
                f"Using default."
            )
            return default

        # Prevent config overwrite
        if os.path.abspath(target_path) == os.path.abspath(config_path):
            print("Warning: Highscore file cannot overwrite active config.")
            return default

        # Block path injection to source folders
        clean_path = target_path.replace("\\", "/")
        if any(dir_name in clean_path.lower() for dir_name in [
            "pacman/", "docs/", "wheel/"
        ]):
            print(
                "Warning: Cannot write highscores inside source folders. "
                "Relocating to root."
            )
            return base_name

        env_dir = os.environ.get("VIRTUAL_ENV")
        if not env_dir and sys.prefix != sys.base_prefix:
            env_dir = sys.prefix

        if env_dir:
            abs_target = os.path.abspath(target_path)
            abs_env = os.path.abspath(env_dir)
            if abs_target.startswith(abs_env):
                print(
                    "Warning: Cannot write highscores inside the "
                    "environment folder. Relocating to root."
                )
                return base_name

        return target_path

    def load_from_disk(self) -> None:
        """Loads and validates highscores from a persistent JSON file.

        Streams structural rows into add_score to safely compile records.
        """
        if not os.path.exists(self.filename):
            self.scores = []
            return

        try:
            with open(self.filename, "r") as file:
                raw_data = json.load(file)

            if not isinstance(raw_data, list):
                raise OSError("Highscores must be a list")
            self.scores = []  # Clear in-memory board before rebuilding
            for item in raw_data:
                if not isinstance(item, dict):
                    continue
                if "name" not in item or "score" not in item:
                    continue
                try:
                    clean_score = int(item["score"])
                except (ValueError, TypeError):
                    continue
                self.add_score(str(item["name"]), clean_score)

        except (OSError, json.JSONDecodeError) as e:
            print(
                f"Warning: Failed to load highscores ({e}). "
                f"Using empty leaderboard."
            )
            self.scores = []

    def save_to_disk(self) -> None:
        """Serializes and saves active top 10 scores array to disk."""
        try:
            with open(self.filename, "w") as file:
                json.dump(self.scores, file, indent=4)
        except OSError as e:
            print(f"Warning: Failed to save highscores ({e}).")

    def add_score(self, name: str, score: int) -> None:
        """Sanitizes, inserts, sorts, and truncates a new highscore entry.

        Args:
            name: The player's inputted name or initials.
            score: The final game score achieved by the player.
        """
        clean_name = "".join(
            c for c in name if c.isalnum() or c == " "
        )[:10].strip()
        if not clean_name:
            clean_name = "Unknown"

        clean_score = max(0, score)
        self.scores.append({"name": clean_name, "score": clean_score})

        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]

    def best(self) -> int:
        """Returns the highest score on the leaderboard, or 0 if empty.

        Returns:
            The top score currently recorded.
        """
        if not self.scores:
            return 0
        return int(self.scores[0]["score"])
