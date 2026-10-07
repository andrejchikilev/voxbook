# AGENTS.md

## Setup
- Use `uv`; the project targets Python `3.14` via `.python-version` and `requires-python`.
- Install deps with `uv sync --dev`; CI uses `uv sync --all-extras --dev`.

## Commands
- Lint: `make lint` or `uv run ruff check .`
- Format: `make format` or `uv run ruff format .`
- Tests: `make test` or `uv run pytest -v`
- Focused test: `uv run pytest tests/path/test_file.py::test_name -v`
- Pylint CI command: `uv run pylint $(git ls-files "*.py")`

## Architecture
- CLI entrypoint is `voxbook.cli:app` from `pyproject.toml`; `src/voxbook/main.py` is not the real app entrypoint.
- SQLite DB path is hardcoded in `src/voxbook/storage/db.py` as `~/.local/share/voxbook/voxbook.db`.
- DB tables are created with `SQLModel.metadata.create_all(engine)` in the Typer callback; there are no migrations.
- Library scanning lives in `src/voxbook/library/scanner.py`; scan pattern order matters: book-folder-with-parts, nested-inherited-name, flat-book-folder, single-file.
- Playback orchestration is in `src/voxbook/playback/player_service.py`; real playback requires `mpv`, but unit tests use mocks.
- `src/voxbook/tui/app.py` and `src/voxbook/config.py` currently exist but are empty.

## Testing Gotchas
- Tests may import storage modules that create `~/.local/share/voxbook`; avoid assuming tests use an isolated DB unless you add explicit patching.
- For playback changes, prefer injecting/mocking `MpvController` or `PlaybackRepository` instead of invoking real `mpv`.
- Audio validation caches paths in module-level sets; clear with `clear_audio_validation_cache()` when tests depend on changed file validity.

## Style And CI
- Ruff config only enforces `E`, `F`, and `I`; line length is `100`, quote style is double quotes.
- Pre-commit runs end-of-file/trailing-whitespace hooks, Ruff with `--fix`, and Pylint on changed Python files.
- Pylint intentionally disables missing docstrings and several complexity warnings; don’t add docstrings just to satisfy Pylint.
