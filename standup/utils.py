import csv
import logging

from datetime import datetime, timedelta
from windows_toasts import Toast, ToastDuration, WindowsToaster

from .models import ActivityType, AppConfig


def show_notification(header: str, line1: str, line2: str = ""):
    """Displays a Windows notification."""
    try:
        toaster = WindowsToaster("Activity Monitor")
        new_toast = Toast(
            [header, line1, line2] if line2 else [header, line1],
            duration=ToastDuration.Long,
        )
        toaster.show_toast(new_toast)
        logging.info(f"Notification: {header} - {line1}")
    except Exception as e:
        logging.error(f"Failed to show notification: {e}")


def log_to_csv(
    config: AppConfig,
    activity_type: ActivityType,
    start: float,
    end: float,
    duration: float,
):
    """Logs a session to the CSV file."""
    file_exists = config.csv_file.exists()

    try:
        with config.csv_file.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")

            if not file_exists:
                writer.writerow(
                    ["Activity Type", "Start Time", "End Time", "Duration (HH:MM:SS)"]
                )

            writer.writerow(
                [
                    activity_type,
                    datetime.fromtimestamp(start).astimezone().isoformat(),
                    datetime.fromtimestamp(end).astimezone().isoformat(),
                    format_duration(duration),
                ]
            )

        logging.info(
            f"Logged to CSV: {activity_type} session of {format_duration(duration)}"
        )
    except IOError as e:
        logging.error(f"Failed to write to CSV: {e}")


def format_duration(seconds: float) -> str:
    """Formats seconds into a human-readable HH:MM:SS string."""
    return str(timedelta(seconds=int(seconds)))
