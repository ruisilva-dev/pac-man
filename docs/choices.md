# Technical Choices & Rationale

This document tracks the explicit design decisions made during development.

## 1. Environment Management
* **Choice:** Using `uv` for package installation and environment isolation.
* **Rationale:** It provides deterministic builds through lockfiles (`uv.lock`), ensuring that peer reviewers recreate the exact same runtime setup cleanly without broken dependencies.

## 2. Environment Variable Injection via Makefile
* **Choice:** Adding `export UV_SKIP_WHEEL_FILENAME_CHECK=1` directly into the `Makefile`.
* **Rationale:** Fulfills the requirement to use the assigned library without modifying the wheel, ensuring the project builds on any environment via `make install` automatically.

## 3. Graphics Framework Selection
* **Choice:** Pygame Library.
* **Rationale:** Selected to fulfill the Chapter IV mandate for a simple graphical library. It provides native support for 2D primitive geometry rendering, window state management, and real-time event loops required to construct a responsive interactive user interface.

## 4. Physics and Simulation Timing Architecture
* **Choice:** Frame-independent Delta-Time (`dt`) grid interpolation.
* **Rationale:** Instead of locking coordinate updates directly to the hardware frame rate, the core simulation scales position changes smoothly based on elapsed seconds using fractional cell progress interpolation. This guarantees that entities travel at uniform physical velocities across any monitor refresh rate.

## 5. Configuration Parsing Strategy
* **Choice:** Reflective Dataclass Schema Factory.
* **Rationale:** Avoids cascading conditional boilerplate blocks while remaining 100% compliant under `mypy --strict` rules. It dynamically validates incoming types using native fields inspection, ensuring smooth scalability when adding new game parameters.

## 6. Highscore Data Persistence & Overwrite Protection
* **Choice:** Absolute path resolution shielding with dynamic environment isolation via `sys.prefix`.
* **Rationale:** Prevents runtime data persistence loops from corrupting critical game assets or user configurations. By evaluating paths at runtime using full system resolution instead of brittle hardcoded blacklists, the manager blocks malicious or accidental source code directory overwrites while handling variable virtual environment configurations seamlessly.

## 7. Polymorphic Item Consumption Architecture
* **Choice:** Abstract Base Class (`Consumable`) using template method hooks (`on_consume`).
* **Rationale:** Decouples the engine's movement grid from specific item logic. By allowing objects like `Pacgum` and `SuperPacgum` to define their own execution behavior when eaten, the engine can blindly trigger `.on_consume(self)` without running clumsy type-checking conditionals (`isinstance`) across different collectible variants.

## 8. Scene-Based State Machine
* **Choice:** Implementing a polymorphic `Scene` hierarchy for game state management.
* **Rationale:** Avoids creating a monolithic, unreadable main loop filled with `if/else` flags for menus, gameplay, and pause states. It allows each discrete visual state to autonomously handle its own events, updates, and memory cleanup (`on_exit`).

## 9. Strict Decoupling (Logic vs. Rendering)
* **Choice:** Isolating mathematical grid simulation (`PacmanEngine`) completely from visual presentation (`GameRenderer`).
* **Rationale:** The engine only knows about integers, floats, and pure data arrays, while the renderer only handles Pygame surfaces and pixel interpolation. This separation of concerns allows dynamic, real-time graphical theme swapping without risking interference with collision math or game physics.

## 10. UI Overlay Snapshotting
* **Choice:** Capturing a frozen `pygame.Surface` snapshot for `OverlayScene` menus (Pause, Options, Instructions).
* **Rationale:** Instead of constantly re-rendering the hundreds of maze assets and characters live in the background while the game is paused, capturing a single static image and applying a translucent dimming layer saves massive amounts of CPU/GPU overhead and cleanly handles nested menu trees.

## 11. Polymorphic Entity AI 
* **Choice:** Utilizing inheritance for autonomous enemies (`Blinky`, `Pinky`, `Inky`, `Clyde` inheriting from a base `Ghost` class).
* **Rationale:** Respects the Open-Closed Principle (SOLID). Instead of writing a massive update loop filled with `if ghost.type == "blinky"` checks, the engine simply calls `.get_chase_target()`. Each subclass handles its own unique targeting algorithm, making it trivial to extend or alter AI behavior later.

## 12. Centralized Audio Pipeline
* **Choice:** Implementing a globally persistent `AudioManager` initialized at the root `Game` class level.
* **Rationale:** Prevents audio context loss during state transitions. Rather than individual scenes loading and abandoning sound files, the global manager allows music to smoothly persist across menus and levels, guarantees no overlapping track duplications, and provides a centralized endpoint for real-time volume configurations.

## 13. Encapsulated Animation Pacing
* **Choice:** Abstracting frame timing and modulo indexing into standalone `Animator` instances.
* **Rationale:** Protects the renderer from `IndexError` crashes during dynamic asset hotswapping. By embedding the modulo safety clamping directly into an `Animator` object, swapping from a theme with 4 frames to a theme with 1 frame automatically wraps the current index into a legal boundary, preserving structural stability.