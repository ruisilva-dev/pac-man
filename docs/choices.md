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