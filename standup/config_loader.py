import logging
from pathlib import Path
import yaml

from .model.app_config import AppConfig

logger = logging.getLogger(__name__)

SECONDS_PER_MINUTE = 60


class ConfigLoader:
    """YAML configuration file loading and parsing."""

    DEFAULT_ACTIVATION_THRESHOLD_SECONDS = 10
    DEFAULT_CONFIG_FILE = "standup_config.yml"
    DEFAULT_WORK_TIME_MINUTES = 50
    DEFAULT_BREAK_TIME_MINUTES = 3
    DEFAULT_CSV_FILE = "standup_activity_log.csv"
    DEFAULT_STATE_FILE = "standup_last_state.json"
    DEFAULT_TEST_MODE = False
    DEFAULT_BREAK_MESSAGES = [
        "That neck be tired! Do 5 neck rolls - slowly roll your head in a circle! �",
        "You know you thirsty! Walk to the water cooler and back - stay hydrated! �",
        "Life's tough! Do 10 shoulder shrugs - lift those shoulders to your ears! 💪",
        "You're glued to a plasti-glass rectangle! Look out the window for 20 seconds - give your eyes a break! 👀",
        "The butt's been itching for a while now! Walk around your desk 3 times - get that blood flowing! 🚶",
        "Don't bend over backwards, but bend at least a little! Do 5 seated spinal twists - one twist left, one right! 🧘",
        "Wish you chose to live at a farm? Stand up and do 10 calf raises - up on your toes! 🦵",
        "Your mind's going crazy! Take 5 deep breaths - inhale for 4, exhale for 6! 🌬️",
    ]

    DEFAULT_CONFIG_TEMPLATE = """# Standup Activity Monitor Configuration File

# Work duration before break reminder (in minutes)
# Default: 50 minutes
work_time_minutes: 50

# Inactivity duration to be considered a break (in minutes)
# Default: 3 minutes
break_time_minutes: 3

# Seconds of sustained activity required to transition to ACTIVE state
# Default: 10 seconds
# This prevents false positives from brief accidental input
activation_threshold_seconds: 10

# Path to CSV file for logging work/break sessions
# Default: standup_activity_log.csv
csv_file: standup_activity_log.csv

# Path to state file for runtime persistence
# Default: standup_last_state.json
state_file: standup_last_state.json

# Enable test mode (exits after limited duration for testing)
# Default: false
test_mode: false

# Custom break reminder messages (optional)
# A random message will be selected for each break notification
# Default: 8 specific, actionable messages for office work
break_messages:
  - "Do 5 neck rolls - slowly roll your head in a circle! �"
  - "Walk to the water cooler and back - stay hydrated! �"
  - "Do 10 shoulder shrugs - lift those shoulders to your ears! 💪"
  - "Look out the window for 20 seconds - give your eyes a break! 👀"
  - "Walk around your desk 3 times - get that blood flowing! 🚶"
  - "Do 5 seated spinal twists - one twist left, one right! 🧘"
  - "Stand up and do 10 calf raises - up on your toes! 🦵"
  - "Take 5 deep breaths - inhale for 4, exhale for 6! 🌬️"
"""

    def load(self, config_path: Path | None = None) -> AppConfig:
        """Load and parse YAML config; create default if missing."""
        if config_path is None:
            config_path = Path(self.DEFAULT_CONFIG_FILE)

        if not config_path.exists():
            self._create_default_config(config_path)
            logger.info("Created default configuration file at '%s'", config_path)

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                config_data = {}

            logger.info("Loaded configuration from '%s'", config_path)
            return self._parse_config_data(config_data, config_path)

        except yaml.YAMLError as e:
            logger.error("Failed to parse configuration file: %s", e)
            raise
        except (ValueError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error("Failed to load configuration file: %s", e)
            raise

    def _create_default_config(self, config_path: Path) -> None:
        """Create a default configuration file with sensible defaults."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with config_path.open("w", encoding="utf-8") as f:
                f.write(self.DEFAULT_CONFIG_TEMPLATE)
        except Exception as e:
            logger.error("Failed to create default configuration file: %s", e)
            raise

    def _parse_config_data(self, config_data: dict, config_path: Path) -> AppConfig:
        """Parse config dict, fill missing values with defaults, and update file."""
        # Track if we need to update the file
        updated = False

        # Fill in missing values with defaults
        if "work_time_minutes" not in config_data:
            config_data["work_time_minutes"] = self.DEFAULT_WORK_TIME_MINUTES
            updated = True
            logger.warning(
                "Missing 'work_time_minutes' in config, using default: %s",
                self.DEFAULT_WORK_TIME_MINUTES,
            )

        if "break_time_minutes" not in config_data:
            config_data["break_time_minutes"] = self.DEFAULT_BREAK_TIME_MINUTES
            updated = True
            logger.warning(
                "Missing 'break_time_minutes' in config, using default: %s",
                self.DEFAULT_BREAK_TIME_MINUTES,
            )

        if "csv_file" not in config_data:
            config_data["csv_file"] = self.DEFAULT_CSV_FILE
            updated = True
            logger.warning(
                "Missing 'csv_file' in config, using default: %s",
                self.DEFAULT_CSV_FILE,
            )

        if "state_file" not in config_data:
            config_data["state_file"] = self.DEFAULT_STATE_FILE
            updated = True
            logger.warning(
                "Missing 'state_file' in config, using default: %s",
                self.DEFAULT_STATE_FILE,
            )

        work_time_minutes = config_data["work_time_minutes"]
        break_time_minutes = config_data["break_time_minutes"]
        csv_file_path = config_data["csv_file"]
        state_file_path = config_data["state_file"]

        test_mode = config_data.get("test_mode", self.DEFAULT_TEST_MODE)
        activation_threshold = config_data.get(
            "activation_threshold_seconds", self.DEFAULT_ACTIVATION_THRESHOLD_SECONDS
        )
        break_messages = config_data.get("break_messages", self.DEFAULT_BREAK_MESSAGES)

        # Ensure break_messages is a list
        if not isinstance(break_messages, list) or not break_messages:
            break_messages = self.DEFAULT_BREAK_MESSAGES
            config_data["break_messages"] = self.DEFAULT_BREAK_MESSAGES
            updated = True
            logger.warning("Invalid 'break_messages' in config, using defaults")

        # Write updated config back to file if any values were added
        if updated:
            try:
                with config_path.open("w", encoding="utf-8") as f:
                    yaml.dump(
                        config_data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )
                logger.info("Updated configuration file with missing default values")
            except Exception as e:
                logger.error("Failed to update configuration file: %s", e)

        csv_path = Path(csv_file_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        state_path = Path(state_file_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        return AppConfig(
            work_duration_sec=int(work_time_minutes) * SECONDS_PER_MINUTE,
            break_duration_sec=int(break_time_minutes) * SECONDS_PER_MINUTE,
            csv_file=csv_path,
            state_file=state_path,
            test_mode=bool(test_mode),
            activation_threshold_sec=int(activation_threshold),
            break_messages=break_messages,
        )
