"""
Data models and types for the activity monitoring application.

This module defines the core data structures used throughout the application:
- Application state management
- Configuration settings
- Type definitions for activity tracking
"""

from typing import NamedTuple, Literal
from enum import Enum, auto
from pathlib import Path

# Activity type constants for better readability
WORK_ACTIVITY = "Work"
BREAK_ACTIVITY = "Break"


class State(Enum):
    """Represents the current state of the activity monitor."""

    IDLE = auto()
    ACTIVE = auto()


type ActivityType = Literal["Work", "Break"]


def state_to_activity(state: State) -> ActivityType:
    """
    Converts a State enum to a human-readable activity string.

    Args:
        state: The current application state

    Returns:
        "Work" for ACTIVE state, "Break" for IDLE state
    """
    return WORK_ACTIVITY if state == State.ACTIVE else BREAK_ACTIVITY


class AppConfig(NamedTuple):
    """
    Configuration settings for the application.

    Attributes:
        work_duration_sec: Duration in seconds before break reminder
        break_duration_sec: Inactivity duration to be considered a break
        csv_file: Path to the main activity log file
        test_mode: Whether to run in test mode with limited duration
    """

    work_duration_sec: int
    break_duration_sec: int
    csv_file: Path
    test_mode: bool


class AppState(NamedTuple):
    """
    Holds the current runtime state of the application.

    Attributes:
        current_state: Current state (IDLE or ACTIVE)
        session_start_time: Unix timestamp when current session started
        break_reminder_shown: Whether break reminder has been shown for current session
    """

    current_state: State
    session_start_time: float
    break_reminder_shown: bool
