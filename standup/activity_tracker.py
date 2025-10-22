"""
Activity tracking and global state management.

This module manages the global activity state and provides callbacks
for input event detection used by the state machine.
"""

import time

# Global state for activity tracking
last_activity_time = time.time()
last_activity_monotonic = time.monotonic()


def on_activity(x=None, y=None, button=None, pressed=None, key=None):
    """
    Callback for input listeners to update the global last activity time.

    This function is called whenever mouse or keyboard activity is detected
    and updates the global timestamp used by the state machine.

    Args:
        x, y: Mouse coordinates (optional)
        button: Mouse button (optional)
        pressed: Button press state (optional)
        key: Keyboard key (optional)
    """
    global last_activity_time, last_activity_monotonic
    last_activity_time = time.time()
    last_activity_monotonic = time.monotonic()


def get_last_activity_time() -> float:
    """
    Get the timestamp of the last detected activity.

    Returns:
        Timestamp of last activity
    """
    return last_activity_time


def set_last_activity_time(timestamp: float, monotonic_timestamp: float | None = None):
    """
    Set the last activity time (used during initialization).

    Args:
        timestamp: New timestamp for last activity
    """
    global last_activity_time, last_activity_monotonic
    last_activity_time = timestamp
    if monotonic_timestamp is None:
        last_activity_monotonic = time.monotonic()
    else:
        last_activity_monotonic = monotonic_timestamp


def get_last_activity_monotonic() -> float:
    """
    Get the monotonic timestamp of the last detected activity.

    Returns:
        Monotonic timestamp of last activity
    """
    return last_activity_monotonic
