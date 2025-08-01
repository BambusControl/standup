# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Created dedicated modules for better separation of concerns:
  - `activity_tracker.py` - Global activity state management
  - `thread_manager.py` - Thread lifecycle management
  - `input_listeners.py` - Input event listeners
  - `event_buffer.py` - Thread-safe event buffering
  - `window_monitor.py` - Active window monitoring
  - `raw_data_logger.py` - Raw data CSV logging
  - `activity_aggregator.py` - Activity data aggregation

### Changed
- Significantly improved code readability and maintainability following Python best practices
- Refactored `data_collector.py` to serve as a high-level API coordinator
- Split monolithic modules into focused, single-responsibility components
- Enhanced modular architecture with clear separation between data collection, state management, and UI
- Improved error handling and defensive programming throughout
- Applied consistent naming conventions and documentation standards

### Fixed
- Eliminated code duplication through proper abstraction
- Reduced cyclic dependencies between modules
- Improved thread safety in event collection systems

## [0.2.0] - 2025-08-01

### Added

- Implemented `--test` flag for controlled application execution.
- Added active window monitoring to data collection, logging window titles.
- Introduced per-second summary logging for raw activity data.
- Added activity monitoring and data collection functionality.
- Implemented data collection for mouse and keyboard events.

### Changed

- Synchronized data collection and window polling intervals to a shared constant (5 seconds).
- Refactored `main` function for improved readability and modularity.
- Modularized the application into a `monitor` package.
- Updated CLI entry points to use `pyproject.toml` and `__main__.py` for runnable module.
- Renamed project from `stand-up` to `standup`.
- Refactored activity monitor structure and updated dependency management documentation.

### Fixed

- Ensured consistent logging of active window titles across all data points.
- Resolved `RuntimeError: threads can only be started once` by refining thread management.
- Corrected `NameError` for `threading` import.
- Removed `last_process_name` column from raw activity data due to consistent null values.

### Chore

- Removed unused line from `pyproject.toml`.
- Integrated `ruff` for code linting and formatting.
