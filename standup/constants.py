"""
Application-wide constants for the activity monitoring system.

This module contains constants that are shared across multiple modules
to ensure consistency and avoid duplication.
"""

# Data collection timing constants
COLLECTION_INTERVAL_SECONDS = 5
"""Interval in seconds between data collection cycles."""

WINDOW_POLL_INTERVAL_SECONDS = 1
"""Interval in seconds between window title polling to get more frequent updates."""
