# Standup: Activity Monitor

A simple Python-based activity monitor for Windows. This script tracks keyboard and mouse input to distinguish between active work sessions and breaks. It provides desktop notifications to remind you to take breaks after a configurable period of continuous work and logs all activity to a CSV file for later review.

## Features

*   Monitors keyboard and mouse activity.
*   Sends Windows toast notifications to remind you to take a break.
*   Logs work and break sessions to `activity_log.csv`.
*   Configurable work and break time durations.
*   **Detailed raw activity logging to `raw_activity.csv` (or `raw_activity_test.csv` in test mode) for data science experiments.**
    *   Includes mouse movements, clicks, scrolls, key presses.
    *   **Per-second summary of activity counts.**
    *   **Active window title logging to understand context (e.g., application in use).**
*   **Command-Line Interface (CLI) using `click` for easy control.**
*   **Test mode (`--test`) for controlled execution and data generation.**

## Technology

*   Python
*   `pynput` for input monitoring.
*   `windows-toasts` for notifications.
*   `click` for command-line interface.
*   `pygetwindow` for active window monitoring.
*   `ruff` for code linting and formatting.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/standup.git
    cd standup
    ```

2.  **Set up a virtual environment and install dependencies:**
    ```bash
    uv sync
    uv pip install -e .
    ```

## Usage

To start the activity monitor:

```bash
monitor start
```

To see available options:

```bash
monitor start --help
```

Example: Run in test mode for 16 seconds (3 intervals of 5 seconds + 1 second buffer):

```bash
monitor start --test
```