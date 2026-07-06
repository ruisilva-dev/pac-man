*This project has been created as part of the 42 curriculum by ruisilva, luida-cu.*

## Description
This project is a modern Python recreation of the famous 1980 arcade game, Pac-Man. Built using Object-Oriented Programming and the Pygame library, the goal of this project is to breathe new life into the classic title while adhering to strict modern software architecture principles. It features authentic ghost AI (Blinky, Pinky, Inky, and Clyde), an extra life scoring system, procedural maze generation, and a fully decoupled rendering pipeline supporting real-time theme swapping.

## Instructions
The project relies on the uv package manager for dependency management and requires Python 3.10 or later. 

**Installation:**
To install the necessary dependencies and the external maze generator wheel, use the provided Makefile:

```bash
make install
```

**Execution:**
Launch the game by providing a valid configuration file:

```bash
make run
```

**Additional Commands:**
* **make debug:** Runs the game through the built-in Python pdb debugger.
* **make lint:** Runs strict static analysis using flake8 and mypy.
* **make lint-strict:** Same as *make lint* but with mypy --strict
* **make clean:** Removes caching directories and artifacts.

## Configuration
The game loads parameters from a config.json file. The custom parser supports standard JSON as well as stripping lines starting with a hash symbol to allow for comments. Missing or invalid keys are gracefully clamped to safe defaults without crashing.

**Available Keys & Defaults:**
* `highscore_filename` (str): Target storage file for leaderboards (default: "highscore.json").
* `lives` (int): Number of starting attempts, clamped between 1 and 5 (default: 3).
* `seed` (int): Deterministic seed for the level 1 maze generation (default: 42).
* `points_per_pacgum` (int): Score yielded per standard dot (default: 10).
* `points_per_super_pacgum` (int): Score yielded per power pellet (default: 50).
* `points_per_ghost` (int): Score yielded for eating a frightened ghost (default: 200).
* `theme` (str): Visual asset pack to load, or "auto" for progression (default: "auto").
* `window_width` (int): Fixed width of the application window (default: 960).
* `window_height` (int): Fixed height of the application window (default: 1000).

## Highscore
The game features a persistent top-10 leaderboard system.

**How it works:** Scores and player names (up to 10 alphanumeric characters) are serialized into a local JSON file array. It loads upon game initialization and saves to disk immediately after a game-over or victory name entry.

**Why it was implemented this way:** JSON provides a lightweight, human-readable storage format that does not require a heavy database engine. To prevent malicious or accidental overwrites of critical source files, the HighscoreManager utilizes absolute path resolution shielding. It explicitly blocks writes to source directories and safely relocates the output to the environment root, ensuring data persistence loops cannot corrupt game assets.

## Maze Generation
The game dynamically generates level layouts using the externally assigned A-Maze-ing package.

The engine interfaces with the MazeGenerator constructor, passing the target size and seed. By setting perfect=False, the generator produces classic Pac-Man style loops and corridors rather than strict dead-end labyrinths. The engine parses the resulting 2D bitmask grid (where 15 represents a 4-wall block) into physical coordinates. Standard pacgums are distributed intelligently by identifying and spawning only on cells with 2 or 3 walls, intentionally leaving 3-way and 4-way intersections blank to match the continuous-line aesthetic of the original arcade game.

## Implementation
The application is written strictly in Python >=3.10 and adheres entirely to the flake8 coding standard. Type safety is strictly enforced via mypy, completely eliminating dynamic typing ambiguity.

Physics and movement are driven by a frame-independent delta-time (dt) interpolation system. Rather than locking grid updates to the hardware framerate, entities transition smoothly between grid cells using fractional progress floats, ensuring consistent simulation speed on any monitor refresh rate. Error handling uses contextual try-except blocks (especially during IO operations for highscores and configs) to ensure the application fails gracefully without Python tracebacks.

## General Software Architecture
The software utilizes a strict separation of concerns alongside a polymorphic State Machine.

* **State Machine (Scenes):** The main Game loop delegates entirely to polymorphic Scene objects (MenuScene, GameScene, OptionsScene, etc.). A subclassed OverlayScene is used to capture frozen pygame. Surface snapshots of the game, allowing menus to sit over a translucent background without continuously re-rendering the heavy simulation.
* **Logic Core (Engine):** The PacmanEngine and its sub-entities (Player, Ghost, Consumable) handle pure math, coordinate state, and BFS pathfinding. It has absolutely no knowledge of Pygame surfaces or graphics.
* **AI (Ghosts):** Ghost logic relies on polymorphic inheritance. The engine triggers get_chase_target() blindly, while dedicated subclasses (Blinky, Pinky, Inky, Clyde) encapsulate their own unique targeting algorithms based on the player's vector and state.
* **Rendering (View):** The GameRenderer maps the pure data grid from the engine into visual assets loaded dynamically by the AssetLoader. Frame timing is abstracted into Animator utilities to prevent IndexError crashes when hotswapping themes with varying sprite counts.
* **Audio:** A global AudioManager sits at the root application level, allowing looping soundtracks to persist seamlessly across scene transitions.

## Project Management
The project was driven using a structured, team-based workflow. Work was divided functionally, with visual/UI orchestration handled by luida-cu, and engine/backend architecture handled by ruisilva.

All progress, risks, architectural choices, and chronological timelines were actively tracked and documented in dedicated markdown files.

For a detailed overview of the timeline, task assignments, and technical choices made during development, please refer to the [docs](./docs/) directory.

## Resources
* **Pygame Documentation:** https://www.pygame.org/docs/
* **The Pac-Man Dossier:** An invaluable breakdown of the original 1980 arcade ghost targeting AI, pathfinding logic, and scatter/chase timings.
* **AI Usage:** Artificial Intelligence was utilized as an interactive pair-programming partner during development. Specifically, AI was used to:
  1. Assist in debugging complex logic and linter errors.
  2. Brainstorm and refine programmatic math logic.
  3. Design atomic Git commit groupings to maintain a clean, logical version control history.
  4. Assist in designing this file.