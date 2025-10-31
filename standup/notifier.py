import logging
from typing import cast

from windows_toasts import Toast, ToastDuration, WindowsToaster

logger = logging.getLogger(__name__)


class Notifier:
    """Windows toast notification display."""

    APP_NAME = "Standup!"

    def show(self, header: str, line1: str, line2: str = ""):
        """Display Windows toast notification with header and message lines."""
        try:
            toaster = WindowsToaster(self.APP_NAME)
            message_lines = self._create_message_lines(header, line1, line2)

            new_toast = Toast(
                text_fields=cast(list[str | None], message_lines),
                duration=ToastDuration.Long,
            )
            toaster.show_toast(new_toast)
            logger.info("Notification: %s - %s", header, line1)
        except Exception as e:
            logger.error("Failed to show notification", exc_info=e)

    def _create_message_lines(self, header: str, line1: str, line2: str = "") -> list:
        """Create message lines list for toast notification."""
        message_lines = [header, line1]
        if line2:
            message_lines.append(line2)
        return message_lines
