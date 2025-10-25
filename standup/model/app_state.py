from typing import NamedTuple

from .state import State


class AppState(NamedTuple):
    """Runtime state: current state, session timestamps, activation tracking."""

    current_state: State
    session_start_time: float
    session_start_monotonic: float
    activation_candidate_start_monotonic: float | None
    break_reminder_shown: bool
