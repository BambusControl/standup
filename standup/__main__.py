"""
Entry point for running the standup module as a script.

This module allows the standup package to be executed directly with:
    python -m standup
"""

from standup.cli import cli


if __name__ == "__main__":
    cli()
