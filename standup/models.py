"""Data models for activity monitoring: AppConfig, AppState, State enum."""

from typing import NamedTuple, Literal
from enum import Enum, auto
from pathlib import Path

# Activity type constants for better readability
WORK_ACTIVITY = "Work"
BREAK_ACTIVITY = "Break"


class State(Enum):
    """Activity monitor state: IDLE or ACTIVE."""

    IDLE = auto()
    ACTIVE = auto()


type ActivityType = Literal["Work", "Break"]


def state_to_activity(state: State) -> ActivityType:
    """Convert State enum to activity string: ACTIVE → 'Work', IDLE → 'Break'."""
    return WORK_ACTIVITY if state == State.ACTIVE else BREAK_ACTIVITY


class AppConfig(NamedTuple):
    """Application configuration with durations, file paths, and thresholds."""

    work_duration_sec: int
    break_duration_sec: int
    csv_file: Path
    state_file: Path
    test_mode: bool
    activation_threshold_sec: int


class AppState(NamedTuple):
    """Runtime state: current state, session timestamps, activation tracking."""

    current_state: State
    session_start_time: float
    session_start_monotonic: float
    activation_candidate_start_monotonic: float | None
    break_reminder_shown: bool
