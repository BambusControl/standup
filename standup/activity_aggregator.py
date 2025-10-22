"""
Activity data aggregation and summarization.

This module handles the aggregation of raw activity events into time-based
summaries for logging and analysis.
"""

import time
from typing import Dict, List

from .event_buffer import (
    EVENT_TYPE_MOUSE_MOVE,
    EVENT_TYPE_MOUSE_CLICK,
    EVENT_TYPE_MOUSE_SCROLL,
    EVENT_TYPE_KEY_PRESS,
    EVENT_TYPE_WINDOW_POLL,
)

# Constants for activity tracking
INITIAL_ACTIVITY_COUNT = 0
MAX_WINDOW_TITLES = 5

# Private module state
_last_known_window_titles = []


def _safe_get_window_title(window_titles: List[str], index: int) -> str:
    """
    Safely get a window title at the specified index.

    Args:
        window_titles: List of window titles
        index: Index to access

    Returns:
        Window title at index, or empty string if index is out of range
    """
    return window_titles[index] if index < len(window_titles) else ""


def aggregate_events_to_summary(events: List[Dict]) -> Dict:
    """
    Aggregate a list of events into a summary dictionary.

    Args:
        events: List of event dictionaries to aggregate

    Returns:
        Dictionary containing aggregated activity counts and metadata
    """
    global _last_known_window_titles

    # Initialize activity counters
    activity_counters = {
        "mouse_moves": INITIAL_ACTIVITY_COUNT,
        "mouse_clicks": INITIAL_ACTIVITY_COUNT,
        "mouse_scrolls": INITIAL_ACTIVITY_COUNT,
        "key_presses": INITIAL_ACTIVITY_COUNT,
    }

    current_window_titles = _last_known_window_titles.copy()
    has_activity_detected = False

    # Process each event
    for event in events:
        event_type = event["event_type"]

        if event_type == EVENT_TYPE_MOUSE_MOVE:
            activity_counters["mouse_moves"] += 1
            has_activity_detected = True
        elif event_type == EVENT_TYPE_MOUSE_CLICK:
            activity_counters["mouse_clicks"] += 1
            has_activity_detected = True
        elif event_type == EVENT_TYPE_MOUSE_SCROLL:
            activity_counters["mouse_scrolls"] += 1
            has_activity_detected = True
        elif event_type == EVENT_TYPE_KEY_PRESS:
            activity_counters["key_presses"] += 1
            has_activity_detected = True
        elif event_type == EVENT_TYPE_WINDOW_POLL:
            window_titles = event.get("window_titles", [])
            if window_titles:
                current_window_titles = window_titles.copy()
                _last_known_window_titles = current_window_titles

    # Ensure we have exactly the required number of window title slots
    while len(current_window_titles) < MAX_WINDOW_TITLES:
        current_window_titles.append("")

    return {
        "timestamp": time.time(),
        "mouse_moves_count": activity_counters["mouse_moves"],
        "mouse_clicks_count": activity_counters["mouse_clicks"],
        "mouse_scrolls_count": activity_counters["mouse_scrolls"],
        "key_presses_count": activity_counters["key_presses"],
        "active_window_1": _safe_get_window_title(current_window_titles, 0),
        "active_window_2": _safe_get_window_title(current_window_titles, 1),
        "active_window_3": _safe_get_window_title(current_window_titles, 2),
        "active_window_4": _safe_get_window_title(current_window_titles, 3),
        "active_window_5": _safe_get_window_title(current_window_titles, 4),
        "activity_detected": int(has_activity_detected),
    }
