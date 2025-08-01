"""
Active window monitoring functionality.

This module handles polling the active window and extracting window titles
for activity context tracking.
"""

import logging
import threading

import pygetwindow as gw

from .event_buffer import log_window_poll

# Configuration
COLLECTION_INTERVAL_SECONDS = 5
NO_WINDOW_TITLE = "No active window"

# Module state
_polling_stop_event = threading.Event()


def create_window_polling_thread() -> threading.Thread:
    """
    Create a thread for window polling.

    Returns:
        Thread object for window polling (needs to be started)
    """
    return threading.Thread(target=_poll_active_window, daemon=True)


def stop_window_polling():
    """Signal the window polling thread to stop."""
    _polling_stop_event.set()


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
            log_window_poll(window_title)
        except Exception as e:
            logging.error(f"Error polling active window: {e}")

        # Wait before next poll
        _polling_stop_event.wait(COLLECTION_INTERVAL_SECONDS)


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
