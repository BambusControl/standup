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

# Private module state
_last_known_window_title = None


def aggregate_events_to_summary(events: List[Dict]) -> Dict:
    """
    Aggregate a list of events into a summary dictionary.

    Args:
        events: List of event dictionaries to aggregate

    Returns:
        Dictionary containing aggregated activity counts and metadata
    """
    global _last_known_window_title

    # Initialize counters
    activity_counts = {
        "mouse_moves": 0,
        "mouse_clicks": 0,
        "mouse_scrolls": 0,
        "key_presses": 0,
    }

    current_window_title = _last_known_window_title
    activity_detected = False

    # Process each event
    for event in events:
        event_type = event["event_type"]

        if event_type == EVENT_TYPE_MOUSE_MOVE:
            activity_counts["mouse_moves"] += 1
            activity_detected = True
        elif event_type == EVENT_TYPE_MOUSE_CLICK:
            activity_counts["mouse_clicks"] += 1
            activity_detected = True
        elif event_type == EVENT_TYPE_MOUSE_SCROLL:
            activity_counts["mouse_scrolls"] += 1
            activity_detected = True
        elif event_type == EVENT_TYPE_KEY_PRESS:
            activity_counts["key_presses"] += 1
            activity_detected = True
        elif event_type == EVENT_TYPE_WINDOW_POLL:
            current_window_title = event.get("window_title")
            _last_known_window_title = current_window_title

    return {
        "timestamp": time.time(),
        "mouse_moves_count": activity_counts["mouse_moves"],
        "mouse_clicks_count": activity_counts["mouse_clicks"],
        "mouse_scrolls_count": activity_counts["mouse_scrolls"],
        "key_presses_count": activity_counts["key_presses"],
        "last_window_title": current_window_title,
        "activity_detected": int(activity_detected),
    }
