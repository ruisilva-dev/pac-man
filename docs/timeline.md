| Status | Task | Assignee | Target Date | Actual Completion | Notes / Explanations |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 🟢 | Create /docs folder & initialize uv project | Both | 27/05/2026 | 27/05/2026 | Repository structure is ready. |
| 🟢 | Create Makefile with mandatory rules | Both | 27/05/2026 | 27/05/2026 | Required for static analysis and mypy. Added .flake8 to ignore .venv. |
| 🟢 | Implement basic CLI argument validation | Both | 27/05/2026 | 27/05/2026 | Make sure a config file is passed. |
| 🟢 | Define initial engine contract with MazeGenerator integration | Both | 27/05/2026 | 27/05/2026 | Simple grid/coordinate setup. |
| 🟢 | Initialize core project management suite | Both | 27/05/2026 | 27/05/2026 | Created team.md and choices.md. |
| 🟢 | Build Pygame rendering loop & smooth cell interpolation | luida-cu | 29/05/2026 | 28/05/2026 | Graphical window shell and input buffers are fully integrated with zero strict typing errors. |
| 🟢 | Implement robust reflective configuration factory | ruisilva | 29/05/2026 | 28/05/2026 | Added comment-stripping filter, explicit type verification, and edge-case bounds clamping. |
| 🟢 | Optimized Pygame rendering loop & Implemented Maze Sprites | luida-cu | 30/05/2026 | 29/05/2026 | Render Loop Optimized by pre-rendering fixed objects and maze sprite-tiles fully implemented. |
| 🟢 | Implement robust highscore manager | ruisilva | 30/05/2026 | 29/05/2026 | Built path-sanitization guards, custom fallback shield and criteria validation filters. |
| 🟢 | Implement polymorphic item system & engine placement hooks | ruisilva | 30/05/2026 | 30/05/2026 | Built items.py using abstract class hooks; integrated grid-spawn and evaluation triggers in engine. |
| 🟢 | Integrate ghost, item, and death sprites | luida-cu | 02/06/2026 | 02/06/2026 | Assets loaded for classic theme. |
| 🟢 | Centralize physics and rendering constraints | Both | 02/06/2026 | 02/06/2026 | Extracted hardcoded variables into constants.py to decouple dependencies. |
| 🟢 | Implement ghost AI, BFS pathfinding, and behaviors | ruisilva | 03/06/2026 | 04/06/2026 | Added class profiles (Blinky, Pinky, Inky, Clyde). Delayed 1 day to refactor ghost respawn logic, ensuring travel speeds sync perfectly with the strict 5-second penalty. |
| 🟢 | Integrate collision states, death sequences, and HUD | Both | 04/06/2026 | 04/06/2026 | Engine handles grid boundaries, ghost rendering, and frightened triggers. |
| 🟢 | Implement dynamic asset loader and theme caching | luida-cu | 04/06/2026 | 04/06/2026 | Extracted Pygame loading logic into an isolated loader to prevent memory leaks and support theme swapping. |
| 🟢 | Build polymorphic scene architecture (Menus/UI) | luida-cu | 04/06/2026 | 04/06/2026 | Replaced monolithic state-machine with Scene pattern (Menu, Options, Highscore, Game Over, Pause). |
| 🟢 | Implement fixed-aspect letterboxing & viewport scaling | luida-cu | 04/06/2026 | 04/06/2026 | Game loop now renders to a fixed arcade surface before projecting mathematically onto the hardware window. |
| 🟢 | Fix continuous actor collisions & integrate smoothscale | luida-cu | 05/06/2026 | 05/06/2026 | Resolved clipping bug by tracking interpolated coordinates and optimized hardware viewport project scaling. |
| 🟢 | Implement core level metrics & progression data layer | ruisilva | 05/06/2026 | 05/06/2026 | Added level countdown timer, single life timeout penalty, and built dynamic procedural map factory under DRY methods. |

*Status Legend: ⚪ Not Started | 🟡 In Progress | 🟢 Completed*
