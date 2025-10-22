"""CLI for the activity monitor using Click."""

import click
import logging
from pathlib import Path

from .app import run_app
from .config_loader import load_config_from_file


@click.command()
@click.option(
    "--config-file",
    type=click.Path(exists=False, path_type=Path),
    help="Path to YAML configuration file (default: standup_config.yml).",
)
def start(config_file: Path | None):
    """Start the activity monitor."""
    _setup_logging()

    # Load configuration from file (or use defaults if file doesn't exist)
    config = load_config_from_file(config_file)

    click.echo("Starting the activity monitor...")
    run_app(config)


def _setup_logging():
    """Configure INFO-level logging."""
    logging.basicConfig(level=logging.INFO)
