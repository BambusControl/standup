# Changelog

All notable changes to this project will be documented in this file.

## [NEXT RELEASE] - Unreleased

### Changed
- Refactored entire codebase to class-based architecture with dependency injection
- Converted `activity_tracker.py` to `ActivityTracker` class
- Converted `config_loader.py` to `ConfigLoader` class
- Converted `state_handlers.py` to `StateHandler` class
- Converted `thread_manager.py` to `ThreadManager` class
- Converted `app.py` to `App` class with comprehensive lifecycle management
- Split `utils.py` into focused classes: `Notifier`, `SessionLogger`, `StatePersistence`
- Split `models.py` into `model/` submodule with separate files:
  - `activity_type.py`: Activity type definitions and constants
  - `state.py`: State enum and conversion logic
  - `app_config.py`: Configuration NamedTuple
  - `app_state.py`: Runtime state NamedTuple
- Cleared `model/__init__.py`: All imports now use explicit full paths
- Moved `COLLECTION_INTERVAL_SECONDS` from `constants.py` into `app.py`
- Updated `__main__.py` to call `cli()` directly
- Removed backwards compatibility `start` alias from `cli.py`

### Fixed
- Fixed shutdown/resume bug where active time wasn't properly simulated during laptop sleep

### Removed
- Deleted `constants.py` file (constant moved to usage location)
- Removed wrapper functions in favor of direct class usage

## [0.4.1] - 2025-10-22

### Added
- Automatic default configuration file creation when `standup_config.yml` is not found
- `DEFAULT_CONFIG_TEMPLATE` with comprehensive comments and sensible defaults

### Changed
- CLI entry point renamed from `start` to `cli` in `cli.py` (with `start` alias for backwards compatibility)
- Configuration loader now creates default config instead of failing when file is missing
- Primary execution method is now `uvx --from ./ standup` for running directly from git

### Fixed
- `ImportError` when running `uvx --from ./ standup` due to missing `cli` function
- First-run experience now seamless - no manual config file creation required

## [0.4.0] - 2025-10-22

### Added
- YAML configuration file support (`standup-config.yml`)
- `config_loader.py` module for parsing YAML configuration with defaults
- `--config-file` CLI option to specify custom configuration file path
- `csv_file` configuration parameter for activity log path
- `state_file` configuration parameter for runtime state persistence path
- Each file type now has its own configurable path

### Changed
- CLI now only accepts `--config-file` parameter; all other configuration via YAML
- File paths now explicitly configured via `csv_file` and `state_file` parameters
- Simplified data collection by removing window monitoring system
- Configuration is now strict: application fails if required fields are missing
- Removed all fallback/default configurations - config file is mandatory
- Updated documentation to reflect configuration file workflow

### Removed
- Raw data logging functionality (`activity_log_raw.csv` files)
- Window monitoring system (`window_monitor.py`, `data_collector.py`)
- `raw_data_logger.py` module
- `activity_aggregator.py` module
- `event_buffer.py` module
- `input_listeners.py` module
- Per-second activity data collection (originally intended for ML analysis)
- CLI parameters for work-time, break-time, csv-file, test, and activation-threshold

## [0.3.0] - 2025-10-22

### Added
- Implemented gamified break reminders with pushup challenge (1 pushup per 10 minutes of work)
- Added `constants.py` module for application-wide shared constants
- Implemented runtime state persistence and resumption across application restarts
- Added monotonic timestamp tracking for more robust duration calculations
- Created `save_runtime_state()`, `load_runtime_state()`, and `clear_runtime_state()` utility functions
- Added support for system sleep/wake detection using dual timestamp approach

### Changed
- Enhanced window polling frequency from 5s to 1s for more accurate active window tracking
- Improved activity aggregation logic with better edge case handling
- Updated state handlers to use monotonic timestamps for session duration calculations
- Refactored break reminder notifications to include personalized pushup goals
- Enhanced thread management with improved lifecycle handling
- Improved raw data logger with more comprehensive error handling
- Updated event buffer implementation for better thread safety
- Refined input listener implementations with enhanced debugging capabilities

### Fixed
- Resolved issues with session duration accuracy during system clock adjustments
- Fixed final state saving to preserve session data correctly on application exit
- Improved handling of activation candidate timing edge cases
- Enhanced error recovery in activity tracking modules
- Fixed potential race conditions in multi-threaded event collection

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

## [NO-RELEASE] - Start of the project before the first released version

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
