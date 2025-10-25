# Project Context: Standup Activity Monitor

See general information about the project in [README.md](README.md).
For a log of changes, see [CHANGELOG.md](CHANGELOG.md).
Always review past changes before contributing, and state the changes you make in your commits, and the changelog under `[NEXT RELEASE]` before making a release version which will change it to the released version.

## Overview

- *Python version*: see [.python-version](.python-version)
- *Tech stack*: using `uv`, see [pyproject.toml](pyproject.toml)
- *Entrypoint*: see [standup/__main__.py](standup/__main__.py)

## Dependency Management
This project uses `uv` for dependency management:
- **Primary execution**: `uv run standup`
- User-default execution: `uvx --from ./ standup` (run directly from git)
- Install dependencies: `uv sync`
- Add dependency: `uv add <package_name>`
- Remove dependency: `uv remove <package_name>`

## Primary logic
- **IDLE → ACTIVE**: Requires sustained activity (default: 10 seconds of continuous input) to prevent false positives
- **ACTIVE → IDLE**: Transitions after configured inactivity period (default: 2 minutes)
- **Break Reminders**: Shown after continuous work period; includes gamified pushup recommendations (1 pushup per 10 minutes of work)
- **Sleep Detection**: Uses both wall-clock and monotonic timestamps to handle system suspend/resume

## Key Design Patterns
- **Class-Based Architecture**: All modules use dependency injection with class instances
- **State Machine**: Clean IDLE/ACTIVE transitions with configurable thresholds
- **Thread-Safe Buffering**: Event collection happens asynchronously
- **Defensive Programming**: Handles system sleep/wake, clock adjustments, thread safety
- **Signal Handling**: SIGINT/SIGTERM handlers for graceful shutdown with state persistence
- **Modular Architecture**: Single-responsibility modules with clear interfaces
- **Immutable Data**: NamedTuples for data structures, state transitions via `._replace()`

## Code Organization
- **Model Submodule**: `standup/model/` contains all data types (NamedTuples, Enums, type aliases)
- **Explicit Imports**: No `__init__.py` re-exports, use full paths like `from .model.app_config import AppConfig`
- **Colocated Constants**: Define constants near their usage, not in separate files
- **Focused Classes**: Each file contains one class with a single, clear responsibility

## Documentation Philosophy
- **Self-Documenting Code**: Code should be clear and readable without extensive documentation
- **Concise Docstrings**: Single-line docstrings that describe what functions/classes do, not how
- **No Args/Returns/Raises**: Type hints provide parameter and return type information
- **Minimal Markdown**: Avoid extensive architecture documentation in README or other markdown files
- **Let Code Speak**: Well-named functions, variables, and clear logic over verbose comments

## Code Style
- Follow PEP 8 conventions
- Use `ruff format` and `ruff check --fix` before committing
- Type hints required for all function parameters and return values
- Single-line docstrings for public classes and methods
- Maximum readability and clarity over cleverness

## Anti-Patterns (Do Not Use)
- ❌ Wrapper functions around classes
- ❌ Module-level global state
- ❌ Verbose docstrings with Args/Returns/Raises sections
- ❌ Re-exporting from `__init__.py` files
- ❌ Constants in separate files away from usage
- ❌ Multi-file refactoring without testing between changes

## Patterns to Follow
- ✅ Dependency injection in class constructors
- ✅ Explicit full-path imports
- ✅ NamedTuples for immutable data structures
- ✅ Single-line docstrings
- ✅ Constants defined at module level where used
- ✅ Test after each logical change
- ✅ Commit frequently with descriptive messages
