"""YAML configuration file loading and parsing."""

import logging
from pathlib import Path
import yaml

from .models import AppConfig

# Set up module-level logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_ACTIVATION_THRESHOLD_SECONDS = 10
DEFAULT_CONFIG_FILE = "standup_config.yml"
DEFAULT_WORK_TIME_MINUTES = 50
DEFAULT_BREAK_TIME_MINUTES = 3
DEFAULT_CSV_FILE = "standup_activity_log.csv"
DEFAULT_STATE_FILE = "standup_last_state.json"
DEFAULT_TEST_MODE = False

# Time conversion constants
SECONDS_PER_MINUTE = 60

# Default config file template
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
"""


def load_config_from_file(config_path: Path | None = None) -> AppConfig:
    """Load and parse YAML config; create default if missing."""
    if config_path is None:
        config_path = Path(DEFAULT_CONFIG_FILE)

    if not config_path.exists():
        _create_default_config(config_path)
        logger.info("Created default configuration file at '%s'", config_path)

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            raise ValueError(
                f"Configuration file '{config_path}' is empty. "
                f"Please provide required configuration values."
            )

        logger.info("Loaded configuration from '%s'", config_path)
        return _parse_config_data(config_data)

    except yaml.YAMLError as e:
        logger.error("Failed to parse configuration file: %s", e)
        raise
    except (ValueError, FileNotFoundError):
        raise
    except Exception as e:
        logger.error("Failed to load configuration file: %s", e)
        raise


def _create_default_config(config_path: Path) -> None:
    """Create a default configuration file with sensible defaults."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)
    except Exception as e:
        logger.error("Failed to create default configuration file: %s", e)
        raise


def _parse_config_data(config_data: dict) -> AppConfig:
    """Parse config dict and validate required fields."""
    # Required fields
    if "work_time_minutes" not in config_data:
        raise ValueError("Configuration must specify 'work_time_minutes'")
    if "break_time_minutes" not in config_data:
        raise ValueError("Configuration must specify 'break_time_minutes'")
    if "csv_file" not in config_data:
        raise ValueError("Configuration must specify 'csv_file' path")
    if "state_file" not in config_data:
        raise ValueError("Configuration must specify 'state_file' path")

    work_time_minutes = config_data["work_time_minutes"]
    break_time_minutes = config_data["break_time_minutes"]
    csv_file_path = config_data["csv_file"]
    state_file_path = config_data["state_file"]

    # Optional fields with defaults
    test_mode = config_data.get("test_mode", False)
    activation_threshold = config_data.get(
        "activation_threshold_seconds", DEFAULT_ACTIVATION_THRESHOLD_SECONDS
    )

    # Create file paths and ensure parent directories exist
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
    )
