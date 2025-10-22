# Standup: Activity Monitor

A Python-based activity monitor for Windows that tracks keyboard and mouse input to distinguish between active work sessions and breaks. Features desktop notifications to remind you to take breaks after configurable periods of continuous work and comprehensive activity logging for detailed analysis.

## Todo

- [ ] Show how many clicks occured during the work session on break reminder
- [ ] Show how far the mouse travelled during the work session on break reminder
- [ ] Show how many characters were typed during the work session on break reminder
- [ ] Show how many times the active window changed during the work session on break reminder
- [ ] Add customizable break reminder message


## Features

*   **Smart Activity Monitoring**: Tracks keyboard and mouse activity with intelligent state management
*   **Break Reminders**: Windows toast notifications to remind you to take breaks
*   **Comprehensive Logging**:
    *   Work and break sessions logged to `activity_log.csv`
    *   Detailed raw activity data to `*_raw.csv` files for data science analysis
    *   Per-second activity summaries including mouse movements, clicks, scrolls, and key presses
    *   Active window title tracking for context analysis
*   **Configurable Durations**: Customizable work and break time thresholds
*   **Command-Line Interface**: Easy control using `click` framework
*   **Test Mode**: Controlled execution for testing and data generation (`--test` flag)
*   **Modular Architecture**: Clean, maintainable codebase with separation of concerns

## Architecture

The application follows a modular design with clear separation of responsibilities:

- **`app.py`** - Main application orchestration and coordination
- **`activity_tracker.py`** - Global activity state management
- **`state_handlers.py`** - State machine logic for IDLE/ACTIVE transitions
- **`data_collector.py`** - High-level API for raw data collection
- **`event_buffer.py`** - Thread-safe event buffering system
- **`input_listeners.py`** - Mouse and keyboard event listeners
- **`window_monitor.py`** - Active window polling and title extraction
- **`raw_data_logger.py`** - CSV logging for raw activity data
- **`activity_aggregator.py`** - Event aggregation and summarization
- **`thread_manager.py`** - Thread lifecycle management
- **`utils.py`** - Notifications, formatting, and utility functions
- **`models.py`** - Data structures and type definitions
- **`cli.py`** - Command-line interface

## Technology Stack

*   **Python 3.12+** - Core language
*   **`pynput`** - Input monitoring
*   **`windows-toasts`** - Desktop notifications
*   **`click`** - Command-line interface
*   **`pygetwindow`** - Active window monitoring
*   **`ruff`** - Code linting and formatting

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/standup.git
    cd standup
    ```

2.  **Set up dependencies using `uv`:**
    ```bash
    uv sync
    ```

## Usage

Start the activity monitor:

```bash
uv run standup start
```

View available options:

```bash
uv run standup start --help
```

Run in test mode (exits after 16 seconds for testing):

```bash
uv run standup start --test
```

## Development

This project uses modern Python development practices:

- **`uv`** for dependency management and virtual environments
- **`ruff`** for linting and code formatting
- **Modular architecture** for maintainability and testing
- **Type hints** throughout for better code clarity
- **Comprehensive documentation** with docstrings

## Contributing

Contributions are welcome! The modular architecture makes it easy to:
- Add new activity tracking features
- Implement additional notification methods
- Extend data analysis capabilities
- Improve the CLI interface

Please ensure code follows the established patterns and includes appropriate documentation.
