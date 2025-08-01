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
from .event_buffer import extract_events_for_interval

# Configuration constants
CSV_HEADER = [
    "timestamp",
    "mouse_moves_count",
    "mouse_clicks_count",
    "mouse_scrolls_count",
    "key_presses_count",
    "last_window_title",
    "activity_detected",
]

COLLECTION_INTERVAL_SECONDS = 5
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8"

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
    """Signal the summary logging thread to stop."""
    _summary_logging_stop_event.set()


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
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(summary_data)
    except IOError as e:
        logging.error(f"Failed to write to raw log file: {e}")


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


def _wait_for_next_interval(interval_start_time: float):
    """
    Wait for the next collection interval, adjusting for processing time.

    Args:
        interval_start_time: Timestamp when the current interval started
    """
    time_to_wait = COLLECTION_INTERVAL_SECONDS - (time.time() - interval_start_time)
    if time_to_wait > 0:
        _summary_logging_stop_event.wait(time_to_wait)
