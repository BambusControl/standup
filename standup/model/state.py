from enum import Enum, auto

from .activity_type import ActivityType, WORK_ACTIVITY, BREAK_ACTIVITY


class State(Enum):
    """Activity monitor state: IDLE or ACTIVE."""

    IDLE = auto()
    ACTIVE = auto()


def state_to_activity(state: State) -> ActivityType:
    """Convert State enum to activity string: ACTIVE → 'Work', IDLE → 'Break'."""
    return WORK_ACTIVITY if state == State.ACTIVE else BREAK_ACTIVITY
