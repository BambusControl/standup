"""
Raw activity data logging to CSV files.

This module handles writing aggregated activity data to CSV files with
proper formatting and error handling.
"""

import csv
import logging
import threading
import time
from pathlib import Path

from .activity_aggregator import aggregate_events_to_summary
from .constants import COLLECTION_INTERVAL_SECONDS
from .event_buffer import extract_events_for_interval

# Set up module-level logger
logger = logging.getLogger(__name__)

# Configuration constants
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8"
HEADER_FILE_POSITION = 0
MINIMUM_WAIT_TIME = 0

# CSV column definitions for better maintainability
WINDOW_TITLE_COLUMNS = [
    "active_window_1",  # Most recent active window
    "active_window_2",  # Second most recent
    "active_window_3",  # Third most recent
    "active_window_4",  # Fourth most recent
    "active_window_5",  # Fifth most recent
]

CSV_HEADER = [
    "timestamp",
    "mouse_moves_count",
    "mouse_clicks_count",
    "mouse_scrolls_count",
    "key_presses_count",
    *WINDOW_TITLE_COLUMNS,
    "activity_detected",
]

# Module state
_summary_logging_stop_event = threading.Event()


def create_summary_logging_thread(log_file: Path) -> threading.Thread:
    """
    Create a thread for summary data logging.

    Args:
        log_file: Path to the CSV file for logging

    Returns:
        Thread object for summary logging (needs to be started)
    """
    return threading.Thread(target=_log_summary_data, args=[log_file], daemon=True)


def stop_summary_logging():
    """Signal the summary logging thread to stop gracefully."""
    _summary_logging_stop_event.set()


def _should_write_header(file_handle) -> bool:
    """
    Check if CSV header should be written based on file position.

    Args:
        file_handle: Open file handle

    Returns:
        True if header should be written, False otherwise
    """
    return file_handle.tell() == HEADER_FILE_POSITION


def write_summary_row(summary_data: dict, log_file_path: Path):
    """
    Write a single summary row to the CSV file.

    Args:
        summary_data: Dictionary containing aggregated activity data
        log_file_path: Path to the CSV file for logging
    """
    if not log_file_path:
        return

    try:
        with log_file_path.open("a", newline="", encoding=CSV_ENCODING) as file:
            writer = csv.DictWriter(
                file, fieldnames=CSV_HEADER, delimiter=CSV_DELIMITER
            )

            # Write header only if file is new or empty
            if _should_write_header(file):
                writer.writeheader()
            writer.writerow(summary_data)
    except IOError as e:
        logger.error("Failed to write to raw log file", exc_info=e)


def _log_summary_data(log_path: Path):
    """
    Process the event buffer and log a summary row at regular intervals.

    This function runs in a separate thread and continuously processes events
    from the buffer, aggregating them into time-based summaries.

    Args:
        log_path: Path to the CSV file for logging summaries
    """
    last_processed_timestamp = time.time()

    while not _summary_logging_stop_event.is_set():
        current_interval_start = time.time()
        events_in_interval = extract_events_for_interval(last_processed_timestamp)
        last_processed_timestamp = current_interval_start

        summary_data = aggregate_events_to_summary(events_in_interval)
        write_summary_row(summary_data, log_path)

        # Wait for the next interval, adjusting for processing time
        _wait_for_next_interval(current_interval_start)


def _calculate_wait_time(interval_start_time: float) -> float:
    """
    Calculate how long to wait for the next interval.

    Args:
        interval_start_time: Timestamp when the current interval started

    Returns:
        Time to wait in seconds (minimum 0)
    """
    elapsed_time = time.time() - interval_start_time
    return max(MINIMUM_WAIT_TIME, COLLECTION_INTERVAL_SECONDS - elapsed_time)


def _wait_for_next_interval(interval_start_time: float):
    """
    Wait for the next collection interval, adjusting for processing time.

    Args:
        interval_start_time: Timestamp when the current interval started
    """
    time_to_wait = _calculate_wait_time(interval_start_time)
    if time_to_wait > MINIMUM_WAIT_TIME:
        _summary_logging_stop_event.wait(time_to_wait)
