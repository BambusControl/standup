# Project Context: Standup Activity Monitor

## Overview
'standup' is a Windows desktop activity monitor written in Python 3.12+ that tracks keyboard and mouse input to distinguish between active work sessions and breaks. It operates as a state machine with IDLE and ACTIVE states, providing desktop notifications and comprehensive activity logging.

## Core Functionality
- **Activity Monitoring**: Tracks keyboard/mouse input with configurable thresholds
- **Break Reminders**: Windows toast notifications after configurable work periods (ie: 60 minutes)
- **Session Logging**: Records work/break sessions to CSV files with timestamps and durations
- **Raw Data Collection**: Detailed per-second activity summaries including mouse movements, clicks, scrolls, key presses, and active window titles
- **State Persistence**: Saves runtime state to resume sessions after application restart
- **Configurable Parameters**: Customizable work duration, break duration, and activation thresholds

## State Machine Logic
- **IDLE → ACTIVE**: Requires sustained activity (ie: 10 seconds of continuous input) to prevent false positives
- **ACTIVE → IDLE**: Transitions after configured inactivity period (ie: 2 minutes)
- **Break Reminders**: Shown after continuous work period; includes gamified pushup recommendations
- **Sleep Detection**: Uses both wall-clock and monotonic timestamps to handle system suspend/resume
 and formatting

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
