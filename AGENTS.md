# Project Context: Standup Activity Monitor

## Overview
'standup' is a Windows desktop activity monitor written in Python 3.12+ that tracks keyboard and mouse input to distinguish between active work sessions and breaks. It operates as a state machine with IDLE and ACTIVE states, providing desktop notifications and comprehensive activity logging.

## Core Functionality
- **Activity Monitoring**: Tracks keyboard/mouse input with configurable thresholds
- **Break Reminders**: Windows toast notifications with gamified pushup challenges after configurable work periods (default: 60 minutes)
- **Session Logging**: Records work/break sessions to CSV files with timestamps and durations
- **State Persistence**: Saves runtime state to resume sessions after application restart
- **Configuration Management**: YAML-based configuration file support with strict validation (no fallbacks)

## State Machine Logic
- **IDLE → ACTIVE**: Requires sustained activity (default: 10 seconds of continuous input) to prevent false positives
- **ACTIVE → IDLE**: Transitions after configured inactivity period (default: 2 minutes)
- **Break Reminders**: Shown after continuous work period; includes gamified pushup recommendations (1 pushup per 10 minutes of work)
- **Sleep Detection**: Uses both wall-clock and monotonic timestamps to handle system suspend/resume

## Technology Stack
- **pynput**: Input monitoring (mouse/keyboard events)
- **windows-toasts**: Desktop notifications
- **click**: Command-line interface
- **pyyaml**: Configuration file parsing
- **ruff**: Code linting and formatting

## Dependency Management
This project uses `uv` for dependency management:
- Install dependencies: `uv sync`
- Add dependency: `uv add <package_name>`
- Remove dependency: `uv remove <package_name>`
- Run the application: `uv run standup start`

## Key Design Patterns
- **State Machine**: Clean IDLE/ACTIVE transitions with configurable thresholds
- **Thread-Safe Buffering**: Event collection happens asynchronously
- **Defensive Programming**: Handles system sleep/wake, clock adjustments, thread safety
- **Signal Handling**: SIGINT/SIGTERM handlers for graceful shutdown with state persistence
- **Modular Architecture**: Single-responsibility modules with clear interfaces

## Documentation Philosophy
- **Self-Documenting Code**: Code should be clear and readable without extensive documentation
- **Concise Docstrings**: Single-line docstrings that describe what functions/classes do, not how
- **No Args/Returns/Raises**: Type hints provide parameter and return type information
- **Minimal Markdown**: Avoid extensive architecture documentation in README or other markdown files
- **Let Code Speak**: Well-named functions, variables, and clear logic over verbose comments
