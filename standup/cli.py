import click
import logging

from pathlib import Path

from .app import run_app
from .models import AppConfig


@click.group()
def cli():
    """A CLI for the Stand-up activity monitor."""
    pass


@cli.command()
@click.option(
    "--work-time", default=60, help="Continuous work time in minutes before a reminder."
)
@click.option(
    "--break-time",
    default=2,
    help="Inactivity time in minutes to be considered a break.",
)
@click.option(
    "--csv-file",
    default="data/activity_log.csv",
    help="Path to the CSV file for logging work/break sessions.",
)
@click.option(
    "--test",
    is_flag=True,
    help="Run in test mode (exits after 2 seconds).",
)
def start(work_time: int, break_time: int, csv_file: str, test: bool):
    """Starts the activity monitor."""
    logging.basicConfig(level=logging.INFO)

    csv_filepath = Path(csv_file)
    csv_filepath.parent.mkdir(parents=True, exist_ok=True)

    config = AppConfig(
        work_duration_sec=work_time * 60,
        break_duration_sec=break_time * 60,
        csv_file=csv_filepath,
        test_mode=test,
    )

    click.echo("Starting the activity monitor...")
    run_app(config)
