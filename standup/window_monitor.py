"""
Active window monitoring functionality.

This module handles polling the active window and extracting window titles
for activity context tracking.
"""

import logging
import threading

import pygetwindow as gw

from .constants import WINDOW_POLL_INTERVAL_SECONDS
from .event_buffer import log_window_poll

# Set up module-level logger
logger = logging.getLogger(__name__)

# Configuration
MAX_WINDOW_TITLES_TO_TRACK = 5
NO_WINDOW_TITLE = "No active window"

# Module state
_polling_stop_event = threading.Event()
_last_window_titles = []  # Track last active window titles


def create_window_polling_thread() -> threading.Thread:
    """
    Create a thread for window polling.

    Returns:
        Thread object for window polling (needs to be started)
    """
    return threading.Thread(target=_poll_active_window, daemon=True)


def stop_window_polling():
    """Signal the window polling thread to stop gracefully."""
    _polling_stop_event.set()


def _update_window_titles_list(window_title: str) -> None:
    """
    Update the global list of recent window titles.

    Args:
        window_title: New window title to add to the list
    """
    global _last_window_titles

    # Skip update if title hasn't changed
    if _last_window_titles and _last_window_titles[0] == window_title:
        return

    # Remove title if it exists elsewhere in the list
    if window_title in _last_window_titles:
        _last_window_titles.remove(window_title)

    # Insert at the beginning (most recent)
    _last_window_titles.insert(0, window_title)

    # Keep only the most recent titles
    if len(_last_window_titles) > MAX_WINDOW_TITLES_TO_TRACK:
        _last_window_titles = _last_window_titles[:MAX_WINDOW_TITLES_TO_TRACK]


def _poll_active_window():
    """
    Periodically poll the active window and log its details.

    This function runs in a separate thread and continuously checks
    the currently active window, logging window title information
    at regular intervals.
    """
    while not _polling_stop_event.is_set():
        try:
            active_window = gw.getActiveWindow()
            window_title = _get_window_title(active_window)

            _update_window_titles_list(window_title)
            log_window_poll(_last_window_titles)
        except Exception as e:
            logger.error("Error polling active window", exc_info=e)

        # Wait before next poll
        _polling_stop_event.wait(WINDOW_POLL_INTERVAL_SECONDS)


def _get_window_title(active_window) -> str:
    """
    Extract window title from active window object.

    Args:
        active_window: Window object from pygetwindow

    Returns:
        Window title string or default message if no window
    """
    if active_window and hasattr(active_window, "title"):
        return active_window.title
    return NO_WINDOW_TITLE
