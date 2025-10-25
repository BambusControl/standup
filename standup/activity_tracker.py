import time


class ActivityTracker:
    """Activity state management for the state machine."""

    def __init__(self):
        """Initialize with current timestamps."""
        self._last_activity_time = time.time()
        self._last_activity_monotonic = time.monotonic()

    def on_activity(self, x=None, y=None, button=None, pressed=None, key=None):
        """Update last activity timestamp."""
        self._last_activity_time = time.time()
        self._last_activity_monotonic = time.monotonic()

    def get_last_activity_time(self) -> float:
        """Return wall-clock timestamp of last activity."""
        return self._last_activity_time

    def get_last_activity_monotonic(self) -> float:
        """Return monotonic timestamp of last activity."""
        return self._last_activity_monotonic

    def set_last_activity_time(
        self, timestamp: float, monotonic_timestamp: float | None = None
    ):
        """Set last activity timestamps for initialization."""
        self._last_activity_time = timestamp
        if monotonic_timestamp is None:
            self._last_activity_monotonic = time.monotonic()
        else:
            self._last_activity_monotonic = monotonic_timestamp
