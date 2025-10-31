# Standup: Activity Monitor

A Python-based activity monitor for Windows that tracks keyboard and mouse input to distinguish between active work sessions and breaks.
Features desktop notifications to remind you to take breaks after configurable periods of continuous work and comprehensive activity logging for detailed analysis.

## Features

*   **Smart Activity Monitoring**: Tracks keyboard and mouse activity with intelligent state management
*   **Break Reminders**: Windows toast notifications with customizable break messages
*   **Session Logging**: Work and break sessions logged to `standup_activity_log.csv`
*   **Configuration File Support**: YAML-based configuration for all settings
*   **State Persistence**: Resumes session state across application restarts and system sleep/wake
*   **Customizable Parameters**: Work time, break time, activation thresholds, and break messages
*   **Command-Line Interface**: Simple startup with optional config file path
*   **Test Mode**: Controlled execution for testing (via config file)
*   **Modular Architecture**: Clean, maintainable codebase with separation of concerns

## Installation & Quick Start

The easiest way to run `standup` is directly from the git repository using `uvx` (in an empty directory):

```console
uvx https://github.com/BambusControl/standup.git
```

On first run, a default `standup_config.yml` file will be automatically created with sensible defaults. You can then edit it to customize your preferences.

### Configuration

The application will automatically create a `standup_config.yml` file on first run with these settings:

*   `work_time_minutes`: Duration before break reminder (default: 50)
*   `break_time_minutes`: Inactivity duration to be considered a break (default: 3)
*   `activation_threshold_seconds`: Sustained activity required to transition to active state (default: 10)
*   `csv_file`: Path to activity log CSV file (default: standup_activity_log.csv)
*   `state_file`: Path to state persistence file (default: standup_last_state.json)
*   `test_mode`: Enable test mode for limited duration execution (default: false)
*   `break_messages`: List of custom break reminder messages (8 defaults provided)

Edit this file to customize your preferences, or use a custom config file path:

```console
uvx https://github.com/BambusControl/standup.git --config-file path/to/config.yml
```
