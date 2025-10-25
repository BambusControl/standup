"""CLI for the activity monitor using Click."""

import click
import logging
from pathlib import Path

from .app import App
from .config_loader import ConfigLoader


@click.command()
@click.option(
    "--config-file",
    type=click.Path(exists=False, path_type=Path),
    help="Path to YAML configuration file (default: standup_config.yml).",
)
def cli(config_file: Path | None):
    """Start the activity monitor."""
    _setup_logging()

    config_loader = ConfigLoader()
    config = config_loader.load(config_file)

    click.echo("Starting the activity monitor...")
    app = App(config)
    app.run()


def _setup_logging():
    """Configure INFO-level logging."""
    logging.basicConfig(level=logging.INFO)
