export UV_SKIP_WHEEL_FILENAME_CHECK=1

install:
	@uv sync

run:
	@uv run python3 pac-man.py config.json

debug:
	@uv run python3 -m pdb pac-man.py config.json

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

clean:
	rm -rf .mypy_cache .pytest_cache
	find . -depth -path "./.venv" -prune -o -name "__pycache__" -exec rm -rf {} +

.PHONY: install run debug lint lint-strict clean

