"""
Activity tracking and global state management.

This module manages the global activity state and provides callbacks
for input event detection used by the state machine.
"""

import time

# Global state for activity tracking
last_activity_time = time.time()


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
    global last_activity_time
    last_activity_time = time.time()


def get_last_activity_time() -> float:
    """
    Get the timestamp of the last detected activity.

    Returns:
        Timestamp of last activity
    """
    return last_activity_time


def set_last_activity_time(timestamp: float):
    """
    Set the last activity time (used during initialization).

    Args:
        timestamp: New timestamp for last activity
    """
    global last_activity_time
    last_activity_time = timestamp
