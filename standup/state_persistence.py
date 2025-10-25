import json
import logging
from pathlib import Path

from .model.app_config import AppConfig

logger = logging.getLogger(__name__)


class StatePersistence:
    """Runtime state persistence to disk for session resumption."""

    ENCODING = "utf-8"

    def save(self, config: AppConfig | None, app_state, last_activity_time: float):
        """Save runtime state to disk for session resumption after restart."""
        state_file = self._get_state_file_path(config)
        state = {
            "current_state": getattr(
                app_state.current_state, "name", str(app_state.current_state)
            ),
            "session_start_time": float(getattr(app_state, "session_start_time", 0)),
            "break_reminder_shown": bool(
                getattr(app_state, "break_reminder_shown", False)
            ),
            "last_activity_time": float(last_activity_time),
        }

        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state), encoding=self.ENCODING)
            logger.info("Saved runtime state to %s", state_file)
        except Exception as e:
            logger.error("Failed to save runtime state", exc_info=e)

    def load(self, config: AppConfig | None):
        """Load previously saved runtime state from disk or return None."""
        state_file = self._get_state_file_path(config)
        if not state_file.exists():
            return None
        try:
            data = json.loads(state_file.read_text(encoding=self.ENCODING))
            logger.info("Loaded runtime state from %s", state_file)
            return data
        except Exception as e:
            logger.error("Failed to load runtime state", exc_info=e)
            return None

    def clear(self, config: AppConfig | None):
        """Remove saved runtime state file if present."""
        state_file = self._get_state_file_path(config)
        try:
            if state_file.exists():
                state_file.unlink()
                logger.info("Cleared saved runtime state at %s", state_file)
        except Exception:
            logger.exception("Failed to clear runtime state file")

    def _get_state_file_path(self, config: AppConfig | None) -> Path:
        """Get state file path from config or raise if missing."""
        if not config:
            raise ValueError("Configuration is required to determine state file path")
        if not hasattr(config, "state_file") or not config.state_file:
            raise ValueError("Configuration must specify state_file path")
        return config.state_file
