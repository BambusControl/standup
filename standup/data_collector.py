"""
Raw activity data collection and logging system.

This module provides the high-level API for starting and stopping the
raw data collection system, coordinating all the individual components.
"""

import logging
from pathlib import Path

from .input_listeners import create_input_listeners
from .window_monitor import create_window_polling_thread, stop_window_polling
from .raw_data_logger import create_summary_logging_thread, stop_summary_logging

# Re-export for backward compatibility
COLLECTION_INTERVAL_SECONDS = 5


def start_data_collection(log_file: Path) -> list:
    """
    Initialize and create the raw data collection system.

    Creates listeners for mouse and keyboard events, along with threads for
    window polling and data aggregation. The returned threads need to be
    started by the caller.

    Args:
        log_file: Path where raw activity data will be logged

    Returns:
        List of thread objects that need to be started
    """
    # Create input listeners
    input_listeners = create_input_listeners()

    # Create background processing threads
    polling_thread = create_window_polling_thread()
    summary_logging_thread = create_summary_logging_thread(log_file)

    logging.info(f"Raw data collection system created. Will log to '{log_file}'")

    return [*input_listeners, polling_thread, summary_logging_thread]


def stop_data_collection():
    """
    Signal all data collection threads to stop.

    This sets the stop events for both the window polling thread and
    the summary logging thread, allowing them to gracefully shutdown.
    """
    stop_window_polling()
    stop_summary_logging()
