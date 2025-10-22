"""Global activity state management for the state machine."""

import time

# Global state for activity tracking
last_activity_time = time.time()
last_activity_monotonic = time.monotonic()


def on_activity(x=None, y=None, button=None, pressed=None, key=None):
    """Update global last activity timestamp."""
    global last_activity_time, last_activity_monotonic
    last_activity_time = time.time()
    last_activity_monotonic = time.monotonic()


def get_last_activity_time() -> float:
    """Return wall-clock timestamp of last activity."""
    return last_activity_time


def set_last_activity_time(timestamp: float, monotonic_timestamp: float | None = None):
    """Set last activity timestamps for initialization."""
    global last_activity_time, last_activity_monotonic
    last_activity_time = timestamp
    if monotonic_timestamp is None:
        last_activity_monotonic = time.monotonic()
    else:
        last_activity_monotonic = monotonic_timestamp


def get_last_activity_monotonic() -> float:
    """Return monotonic timestamp of last activity."""
    return last_activity_monotonic
