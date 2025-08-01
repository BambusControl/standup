"""
Utility functions for notifications, logging, and data formatting.

This module provides common utility functions used throughout the application:
- Windows toast notifications
- CSV logging functionality
- Duration formatting helpers
"""

import csv
import logging
from datetime import datetime, timedelta
from typing import cast

from windows_toasts import Toast, ToastDuration, WindowsToaster

from .models import ActivityType, AppConfig

# Constants for CSV logging
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8"
CSV_COLUMNS = ["Activity Type", "Start Time", "End Time", "Duration (HH:MM:SS)"]

# Notification configuration
NOTIFICATION_APP_NAME = "Activity Monitor"
MINIMUM_SESSION_DURATION_SECONDS = 1


def show_notification(header: str, line1: str, line2: str = ""):
    """
    Displays a Windows toast notification.

    Args:
        header: Notification title
        line1: Primary message line
        line2: Optional secondary message line
    """
    try:
        toaster = WindowsToaster(NOTIFICATION_APP_NAME)
        message_lines = [header, line1, line2] if line2 else [header, line1]

        new_toast = Toast(
            text_fields=cast(list[str | None], message_lines),
            duration=ToastDuration.Long,
        )
        toaster.show_toast(new_toast)
        logging.info(f"Notification: {header} - {line1}")
    except Exception as e:
        logging.error(f"Failed to show notification: {e}")


def log_to_csv(
    config: AppConfig,
    activity_type: ActivityType,
    start_time: float,
    end_time: float,
    duration: float,
):
    """
    Logs a completed session to the CSV file.

    Args:
        config: Application configuration containing CSV file path
        activity_type: Type of activity ("Work" or "Break")
        start_time: Session start timestamp
        end_time: Session end timestamp
        duration: Session duration in seconds
    """
    if not _should_log_session(duration):
        return

    file_exists = config.csv_file.exists()

    try:
        with config.csv_file.open("a", newline="", encoding=CSV_ENCODING) as file:
            writer = csv.writer(file, delimiter=CSV_DELIMITER)

            if not file_exists:
                writer.writerow(CSV_COLUMNS)

            formatted_row = _format_csv_row(
                activity_type, start_time, end_time, duration
            )
            writer.writerow(formatted_row)

        logging.info(
            f"Logged to CSV: {activity_type} session of {format_duration(duration)}"
        )
    except IOError as e:
        logging.error(f"Failed to write to CSV: {e}")


def format_duration(seconds: float) -> str:
    """
    Formats seconds into a human-readable HH:MM:SS string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1:23:45")
    """
    return str(timedelta(seconds=int(seconds)))


def _should_log_session(duration: float) -> bool:
    """
    Determine if a session should be logged based on its duration.

    Args:
        duration: Session duration in seconds

    Returns:
        True if session should be logged, False otherwise
    """
    return duration > MINIMUM_SESSION_DURATION_SECONDS


def _format_csv_row(
    activity_type: ActivityType, start_time: float, end_time: float, duration: float
) -> list[str]:
    """
    Format session data into a CSV row.

    Args:
        activity_type: Type of activity
        start_time: Start timestamp
        end_time: End timestamp
        duration: Duration in seconds

    Returns:
        List of formatted strings for CSV row
    """
    return [
        activity_type,
        datetime.fromtimestamp(start_time).astimezone().isoformat(),
        datetime.fromtimestamp(end_time).astimezone().isoformat(),
        format_duration(duration),
    ]
