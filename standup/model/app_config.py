from typing import NamedTuple
from pathlib import Path


class AppConfig(NamedTuple):
    """Application configuration with durations, file paths, and thresholds."""

    work_duration_sec: int
    break_duration_sec: int
    csv_file: Path
    state_file: Path
    test_mode: bool
    activation_threshold_sec: int
    break_messages: list[str]
