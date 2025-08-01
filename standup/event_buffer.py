"""
Event buffer management for raw activity data collection.

This module provides thread-safe event buffering functionality for collecting
user input events (mouse and keyboard) before they are processed and logged.
"""

import threading
import time
from typing import Dict, List

# Event type constants
EVENT_TYPE_MOUSE_MOVE = "mouse_move"
EVENT_TYPE_MOUSE_CLICK = "mouse_click"
EVENT_TYPE_MOUSE_SCROLL = "mouse_scroll"
EVENT_TYPE_KEY_PRESS = "key_press"
EVENT_TYPE_WINDOW_POLL = "active_window_poll"

# Private module state
_event_buffer: List[Dict] = []
_buffer_lock = threading.Lock()


def log_event(event_data: Dict):
    """
    Add a single event dictionary to the thread-safe buffer.

    Args:
        event_data: Dictionary containing event information with timestamp and type
    """
    with _buffer_lock:
        _event_buffer.append(event_data)


def extract_events_for_interval(last_processed_timestamp: float) -> List[Dict]:
    """
    Extract events from the buffer that occurred since the last processing.

    Args:
        last_processed_timestamp: Timestamp of last processing

    Returns:
        List of event dictionaries for the current interval
    """
    events_in_interval = []

    with _buffer_lock:
        # Extract events that occurred in the last interval
        buffer_index = 0
        while buffer_index < len(_event_buffer):
            if _event_buffer[buffer_index]["timestamp"] >= last_processed_timestamp:
                events_in_interval.append(_event_buffer.pop(buffer_index))
            else:
                buffer_index += 1

    return events_in_interval


def log_mouse_move():
    """Log a mouse movement event."""
    log_event({"timestamp": time.time(), "event_type": EVENT_TYPE_MOUSE_MOVE})


def log_mouse_click():
    """Log a mouse click event."""
    log_event({"timestamp": time.time(), "event_type": EVENT_TYPE_MOUSE_CLICK})


def log_mouse_scroll():
    """Log a mouse scroll event."""
    log_event({"timestamp": time.time(), "event_type": EVENT_TYPE_MOUSE_SCROLL})


def log_key_press():
    """Log a keyboard press event."""
    log_event({"timestamp": time.time(), "event_type": EVENT_TYPE_KEY_PRESS})


def log_window_poll(window_title: str):
    """
    Log a window polling event.

    Args:
        window_title: Title of the active window
    """
    log_event(
        {
            "timestamp": time.time(),
            "event_type": EVENT_TYPE_WINDOW_POLL,
            "window_title": window_title,
        }
    )
