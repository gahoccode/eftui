# Repository Guidelines

## Project Structure & Module Organization

Core application code lives under `vietfrontier/`. Keep orchestration in [vietfrontier/controller.py](/Users/tamle/Projects/eftui/vietfrontier/controller.py) and `main.py`, business logic in `vietfrontier/services/`, terminal rendering in `vietfrontier/renderers/`, and prompt/report UI helpers in `vietfrontier/ui/`. Shared data models belong in `vietfrontier/models.py`. Tests mirror runtime modules under `tests/` such as `tests/test_optimizer.py` and `tests/test_controller.py`.

## Build, Test, and Development Commands

Use `uv` for local development.

- `uv sync` installs runtime and dev dependencies from `pyproject.toml` and `uv.lock`.
- `uv run vietfrontier` starts the terminal efficient-frontier app.
- `uv run python main.py` runs the same entry point directly.
- `uv run pytest -q` runs the test suite.
- `uv run ruff check .` checks lint and import order.
- `uv run vulture` finds unused code.
- `uv export --format requirements-txt --no-emit-project > requirements.txt` regenerates `requirements.txt` after dependency changes.

## Coding Style & Naming Conventions

Target Python `3.13`, 4-space indentation, and strict type hints on function definitions. Add short docstrings where intent is not obvious. Use `snake_case` for modules, functions, and variables, and `PascalCase` for classes. Keep route/controller layers thin and move business logic into service classes. Follow Ruff defaults configured in `pyproject.toml`; do not introduce unused code or broad existence checks for known-required objects.

## Testing Guidelines

Follow TDD: add or update tests before changing behavior. Use `pytest`, keep test files named `tests/test_<module>.py`, and name test functions `test_<behavior>()`. Cover new service logic, controller flows, and renderer behavior. Run `uv run pytest -q` before opening a PR.

## Commit & Pull Request Guidelines

Current history uses Conventional Commit style, for example `feat: initial vietfrontier terminal efficient-frontier explorer`. Continue with prefixes like `feat:`, `fix:`, and `docs:`. PRs should include a concise summary, scope-of-impact analysis, affected files/functions, linked issue if available, and terminal screenshots when UI output changes. Use commit message plus diff as the primary source when updating `CHANGELOG.md`.

## Dependency & Docs Hygiene

Keep `pyproject.toml`, `uv.lock`, and `requirements.txt` aligned whenever dependencies change. If you update contributor or usage docs, keep links consistent across `README.md` and `llms.txt`.
