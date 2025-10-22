# Standup: Activity Monitor

A Python-based activity monitor for Windows that tracks keyboard and mouse input to distinguish between active work sessions and breaks. Features desktop notifications to remind you to take breaks after configurable periods of continuous work and comprehensive activity logging for detailed analysis.

## Todo

- [ ] Add customizable break reminder messages
- [ ] Support multiple notification strategies (pushups, stretches, eye exercises, etc.)
- [ ] Add daily/weekly activity summaries


## Features

*   **Smart Activity Monitoring**: Tracks keyboard and mouse activity with intelligent state management
*   **Break Reminders**: Windows toast notifications with gamified pushup challenges
*   **Session Logging**: Work and break sessions logged to `activity_log.csv`
*   **Configuration File Support**: YAML-based configuration with CLI overrides
*   **State Persistence**: Resumes session state across application restarts
*   **Configurable Parameters**: Customizable work time, break time, and activation thresholds
*   **Command-Line Interface**: Easy control using `click` framework
*   **Test Mode**: Controlled execution for testing (`--test` flag)
*   **Modular Architecture**: Clean, maintainable codebase with separation of concerns

## Technology Stack

*   **Python 3.12+** - Core language
*   **`pynput`** - Input monitoring
*   **`windows-toasts`** - Desktop notifications
*   **`click`** - Command-line interface
*   **`pygetwindow`** - Active window monitoring
*   **`pyyaml`** - Configuration file parsing
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

### Using Configuration File (Recommended)

Create a `standup-config.yml` file in the project root:

```yaml
work_time_minutes: 60
break_time_minutes: 2
activation_threshold_seconds: 10
csv_file: logs/activity_log.csv
state_file: state/last_state.json
test_mode: false
```

Then start the monitor:

```bash
uv run standup start
```

Use a custom config file:

```bash
uv run standup start --config-file path/to/config.yml
```

View all available options:

```bash
uv run standup start --help
```

Run in test mode:

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
