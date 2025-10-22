"""Utility functions for notifications, CSV logging, and state persistence."""

import csv
import json
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import cast

from windows_toasts import Toast, ToastDuration, WindowsToaster

from .models import ActivityType, AppConfig
from typing import Optional

# Set up module-level logger
logger = logging.getLogger(__name__)

# Notification configuration
NOTIFICATION_APP_NAME = "Activity Monitor"
MINIMUM_SESSION_DURATION_SECONDS = 1

# Constants for CSV logging
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8"
HEADER_FILE_POSITION = 0

CSV_COLUMNS = ["Activity Type", "Start Time", "End Time", "Duration (HH:MM:SS)"]


def _create_toast_message(header: str, line1: str, line2: str = "") -> list:
    """Create message lines list for toast notification."""
    message_lines = [header, line1]
    if line2:
        message_lines.append(line2)
    return message_lines


def show_notification(header: str, line1: str, line2: str = ""):
    """Display Windows toast notification with header and message lines."""
    try:
        toaster = WindowsToaster(NOTIFICATION_APP_NAME)
        message_lines = _create_toast_message(header, line1, line2)

        new_toast = Toast(
            text_fields=cast(list[str | None], message_lines),
            duration=ToastDuration.Long,
        )
        toaster.show_toast(new_toast)
        logger.info("Notification: %s - %s", header, line1)
    except Exception as e:
        logger.error("Failed to show notification", exc_info=e)


def _format_timestamps(start_time: float, end_time: float) -> tuple[str, str]:
    """Format start and end timestamps to ISO format strings."""
    formatted_start = datetime.fromtimestamp(start_time).astimezone().isoformat()
    formatted_end = datetime.fromtimestamp(end_time).astimezone().isoformat()
    return formatted_start, formatted_end


def _should_write_csv_header(file_handle) -> bool:
    """Check if CSV header should be written based on file position."""
    return file_handle.tell() == HEADER_FILE_POSITION


def _prepare_session_data(
    activity_type: ActivityType, start_time: float, end_time: float, duration: float
) -> dict:
    """Prepare formatted session data dict for CSV logging."""
    formatted_start, formatted_end = _format_timestamps(start_time, end_time)

    return {
        "Activity Type": activity_type,
        "Start Time": formatted_start,
        "End Time": formatted_end,
        "Duration (HH:MM:SS)": format_duration(duration),
    }


def log_to_csv(
    config: AppConfig,
    activity_type: ActivityType,
    start_time: float,
    end_time: float,
    duration: float,
):
    """Log completed session to CSV file with timestamps and duration."""
    if not config.csv_file:
        return

    if not _should_log_session(duration):
        return

    if config.test_mode:
        # Empty the file before starting during tests
        config.csv_file.write_text("", encoding="utf-8")

    try:
        with config.csv_file.open("a", newline="", encoding=CSV_ENCODING) as file:
            writer = csv.DictWriter(
                file, fieldnames=CSV_COLUMNS, delimiter=CSV_DELIMITER
            )

            # Write header only if file is new or empty
            if _should_write_csv_header(file):
                writer.writeheader()

            session_data = _prepare_session_data(
                activity_type, start_time, end_time, duration
            )
            writer.writerow(session_data)
    except IOError as e:
        logger.error("Failed to write to CSV", exc_info=e)


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS string."""
    return str(timedelta(seconds=int(seconds)))


def _should_log_session(duration: float) -> bool:
    """Check if session duration exceeds minimum threshold for logging."""
    return duration > MINIMUM_SESSION_DURATION_SECONDS


def _get_state_file_path(config: Optional[AppConfig]) -> Path:
    """Get state file path from config or raise if missing."""
    if not config:
        raise ValueError("Configuration is required to determine state file path")
    if not hasattr(config, "state_file") or not config.state_file:
        raise ValueError("Configuration must specify state_file path")
    return config.state_file


def save_runtime_state(
    config: Optional[AppConfig], app_state, last_activity_time: float
):
    """Save runtime state to disk for session resumption after restart."""
    state_file = _get_state_file_path(config)
    state = {
        "current_state": getattr(
            app_state.current_state, "name", str(app_state.current_state)
        ),
        "session_start_time": float(getattr(app_state, "session_start_time", 0)),
        "break_reminder_shown": bool(getattr(app_state, "break_reminder_shown", False)),
        "last_activity_time": float(last_activity_time),
    }

    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state), encoding=CSV_ENCODING)
        logger.info("Saved runtime state to %s", state_file)
    except Exception as e:
        logger.error("Failed to save runtime state", exc_info=e)


def load_runtime_state(config: Optional[AppConfig]):
    """Load previously saved runtime state from disk or return None."""
    state_file = _get_state_file_path(config)
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding=CSV_ENCODING))
        logger.info("Loaded runtime state from %s", state_file)
        return data
    except Exception as e:
        logger.error("Failed to load runtime state", exc_info=e)
        return None


def clear_runtime_state(config: Optional[AppConfig]):
    """Remove saved runtime state file if present."""
    state_file = _get_state_file_path(config)
    try:
        if state_file.exists():
            state_file.unlink()
            logger.info("Cleared saved runtime state at %s", state_file)
    except Exception:
        logger.exception("Failed to clear runtime state file")
