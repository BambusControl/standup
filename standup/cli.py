"""
Command-line interface for the activity monitoring application.

This module provides the CLI commands and options for starting and configuring
the activity monitor. It uses Click for command-line argument parsing.
"""

import click
import logging
from pathlib import Path

from .app import run_app
from .models import AppConfig

# Default configuration values
DEFAULT_WORK_TIME_MINUTES = 60
DEFAULT_BREAK_TIME_MINUTES = 2
DEFAULT_CSV_PATH = "data/activity_log.csv"

# Time conversion constants
SECONDS_PER_MINUTE = 60


@click.group()
def cli():
    """A CLI for the Stand-up activity monitor."""
    pass


@cli.command()
@click.option(
    "--work-time",
    default=DEFAULT_WORK_TIME_MINUTES,
    help="Continuous work time in minutes before a reminder.",
)
@click.option(
    "--break-time",
    default=DEFAULT_BREAK_TIME_MINUTES,
    help="Inactivity time in minutes to be considered a break.",
)
@click.option(
    "--csv-file",
    default=DEFAULT_CSV_PATH,
    help="Path to the CSV file for logging work/break sessions.",
)
@click.option(
    "--test",
    is_flag=True,
    help="Run in test mode (exits after limited duration).",
)
@click.option(
    "--activation-threshold",
    default=10,
    help="Seconds of sustained activity required to change to ACTIVE state.",
)
def start(
    work_time: int,
    break_time: int,
    csv_file: str,
    test: bool,
    activation_threshold: int,
):
    """Starts the activity monitor with the specified configuration."""
    _setup_logging()

    csv_filepath = _ensure_csv_directory_exists(csv_file)
    config = _create_app_config(
        work_time, break_time, csv_filepath, test, activation_threshold
    )

    click.echo("Starting the activity monitor...")
    run_app(config)


def _setup_logging():
    """Configure basic logging for the application with INFO level."""
    logging.basicConfig(level=logging.INFO)


def _ensure_csv_directory_exists(csv_file: str) -> Path:
    """
    Ensure the directory for the CSV file exists.

    Args:
        csv_file: Path to the CSV file as string

    Returns:
        Path object for the CSV file
    """
    csv_filepath = Path(csv_file)
    csv_filepath.parent.mkdir(parents=True, exist_ok=True)
    return csv_filepath


def _create_app_config(
    work_time: int,
    break_time: int,
    csv_filepath: Path,
    test_mode: bool,
    activation_threshold: int,
) -> AppConfig:
    """
    Create application configuration from CLI parameters.

    Args:
        work_time: Work duration in minutes
        break_time: Break duration in minutes
        csv_filepath: Path to CSV log file
        test_mode: Whether to run in test mode

    Returns:
        Configured AppConfig instance
    """
    return AppConfig(
        work_duration_sec=work_time * SECONDS_PER_MINUTE,
        break_duration_sec=break_time * SECONDS_PER_MINUTE,
        csv_file=csv_filepath,
        test_mode=test_mode,
        activation_threshold_sec=activation_threshold,
    )
