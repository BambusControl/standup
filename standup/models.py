from typing import NamedTuple, Literal
from enum import Enum, auto
from pathlib import Path


class State(Enum):
    """Represents the current state of the activity monitor."""

    IDLE = auto()
    ACTIVE = auto()
    QUITTING = auto()


type ActivityType = Literal["Work", "Break"]


def state_to_activity(state: State) -> ActivityType:
    """Converts a State to a human-readable activity string."""
    return "Work" if state == State.ACTIVE else "Break"


class AppConfig(NamedTuple):
    """Configuration settings for the application."""

    work_duration_sec: int
    break_duration_sec: int
    csv_file: Path
    test_mode: bool


class AppState(NamedTuple):
    """Holds the current state of the application."""

    current_state: State
    session_start_time: float
    break_reminder_shown: bool
