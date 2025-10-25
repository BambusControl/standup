import csv
import logging
from datetime import datetime

from .model.activity_type import ActivityType
from .model.app_config import AppConfig
from .utils import format_duration

logger = logging.getLogger(__name__)


class SessionLogger:
    """CSV logging for work/break sessions."""

    DELIMITER = ";"
    ENCODING = "utf-8"
    HEADER_FILE_POSITION = 0
    MINIMUM_SESSION_DURATION_SECONDS = 1
    COLUMNS = ["Activity Type", "Start Time", "End Time", "Duration (HH:MM:SS)"]

    def log(
        self,
        config: AppConfig,
        activity_type: ActivityType,
        start_time: float,
        end_time: float,
        duration: float,
    ):
        """Log completed session to CSV file with timestamps and duration."""
        if not config.csv_file:
            return

        if not self._should_log_session(duration):
            return

        if config.test_mode:
            config.csv_file.write_text("", encoding=self.ENCODING)

        try:
            with config.csv_file.open("a", newline="", encoding=self.ENCODING) as file:
                writer = csv.DictWriter(
                    file, fieldnames=self.COLUMNS, delimiter=self.DELIMITER
                )

                if self._should_write_header(file):
                    writer.writeheader()

                session_data = self._prepare_session_data(
                    activity_type, start_time, end_time, duration
                )
                writer.writerow(session_data)
        except IOError as e:
            logger.error("Failed to write to CSV", exc_info=e)

    def _should_log_session(self, duration: float) -> bool:
        """Check if session duration exceeds minimum threshold for logging."""
        return duration > self.MINIMUM_SESSION_DURATION_SECONDS

    def _should_write_header(self, file_handle) -> bool:
        """Check if CSV header should be written based on file position."""
        return file_handle.tell() == self.HEADER_FILE_POSITION

    def _prepare_session_data(
        self,
        activity_type: ActivityType,
        start_time: float,
        end_time: float,
        duration: float,
    ) -> dict:
        """Prepare formatted session data dict for CSV logging."""
        formatted_start, formatted_end = self._format_timestamps(start_time, end_time)

        return {
            "Activity Type": activity_type,
            "Start Time": formatted_start,
            "End Time": formatted_end,
            "Duration (HH:MM:SS)": format_duration(duration),
        }

    def _format_timestamps(self, start_time: float, end_time: float) -> tuple[str, str]:
        """Format start and end timestamps to ISO format strings."""
        formatted_start = datetime.fromtimestamp(start_time).astimezone().isoformat()
        formatted_end = datetime.fromtimestamp(end_time).astimezone().isoformat()
        return formatted_start, formatted_end
