import json
from dataclasses import dataclass, fields
from typing import Any


@dataclass
class Configuration:
    """Handles parsing, validation, and safety clamping of game configurations.

    Attributes:
        highscore_filename: Target storage path for persistent player scores.
        lives: Total starting attempts allocated to the player instance.
        seed: The deterministic seed value used for initial maze generation.
        points_per_pacgum: Score point yield per standard pacgum consumed.
    """

    highscore_filename: str = "highscore_filename"
    lives: int = 3
    seed: int = 42
    points_per_pacgum: int = 10

    @classmethod
    def load(cls, config_path: str) -> "Configuration":
        """Factory method to load and safely validate a configuration file.

        Args:
            config_path: File system location of the target JSON asset.

        Returns:
            A fully initialized and type-safe Configuration instance.
        """
        raw_data = cls._parse_config_file(config_path)
        clean_kwargs: dict[str, Any] = {}

        for field in fields(cls):
            val = raw_data.get(field.name)
            if val is not None and type(val) is field.type:
                clean_kwargs[field.name] = val
            else:
                if val is not None:
                    print(f"Warning: Invalid type for '{field.name}'. "
                          f"Using default.")
                else:
                    print(f"Warning: Missing '{field.name}' in config. "
                          f"Using default.")
                clean_kwargs[field.name] = field.default

        # Enforce mandatory evaluation bounds clamping rules safely
        clean_kwargs["lives"] = max(1, min(clean_kwargs["lives"], 5))

        return cls(**clean_kwargs)

    @staticmethod
    def _parse_config_file(config_path: str) -> dict[str, Any]:
        """Reads a JSON file while filtering out lines starting with '#'.

        Args:
            config_path: File system location of the target JSON asset.

        Returns:
            A dictionary of loosely parsed raw configuration keys and values.
        """
        if not config_path.endswith(".json"):
            print("Warning: Config must be a JSON file. Using defaults.")
            return {}
        try:
            clean_lines: list[str] = []
            with open(config_path, "r") as file:
                for line in file:
                    if line.strip().startswith("#"):
                        continue
                    clean_lines.append(line)
            clean_json_str = "".join(clean_lines)

            # Intercept empty streams before passing to the parser
            if not clean_json_str.strip():
                print("Warning: Configuration file is empty. "
                      "Using defaults.")
                return {}

            data = json.loads(clean_json_str)
            if isinstance(data, dict):
                return data
            print("Warning: Malformed JSON structure. Using defaults.")
            return {}
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load config ({e}). "
                  f"Using defaults.")
            return {}
