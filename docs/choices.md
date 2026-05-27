# Technical Choices & Rationale

This document tracks the explicit design decisions made during development.

## 1. Environment Management
* **Choice:** Using `uv` for package installation and environment isolation.
* **Rationale:** It provides deterministic builds through lockfiles (`uv.lock`), ensuring that peer reviewers recreate the exact same runtime setup cleanly without broken dependencies.

## 2. Environment Variable Injection via Makefile
* **Choice:** Adding `export UV_SKIP_WHEEL_FILENAME_CHECK=1` directly into the `Makefile`.
* **Rationale:** Fulfills Chapter V.4's rule to use the assigned library without modifying the wheel, ensuring the project builds on any environment via `make install` automatically.