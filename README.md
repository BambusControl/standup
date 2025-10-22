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

## Installation & Quick Start

The easiest way to run `standup` is directly from the git repository using `uvx` (in an empty directory):

```bash
uvx https://github.com/BambusControl/standup.git
```

On first run, a default `standup_config.yml` file will be automatically created with sensible defaults. You can then edit it to customize your preferences.

### Advanced Setup

For development or customization:

```bash
# Install dependencies
uv sync

# Run the application
uv run standup
```

## Usage

### Running the Monitor

**Recommended method** (run directly from git):
```bash
uvx --from ./ standup
```

**Using local installation:**
```bash
uv run standup
```

### Configuration

The application will automatically create a `standup_config.yml` file on first run with these defaults:

```yaml
work_time_minutes: 50
break_time_minutes: 3
activation_threshold_seconds: 10
csv_file: standup_activity_log.csv
state_file: standup_last_state.json
test_mode: false
```

Edit this file to customize your preferences.

### Custom Configuration File

Use a custom config file path:

```bash
uvx --from ./ standup --config-file path/to/config.yml
```

### Command-Line Options

View all available options:

```bash
uvx --from ./ standup --help
```
