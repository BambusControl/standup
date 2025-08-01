"""
Thread lifecycle management for the activity monitoring system.

This module provides utilities for managing the lifecycle of all threads
used in the application, including starting, stopping, and cleanup.
"""

import logging
from typing import List

from pynput import mouse, keyboard


def start_all_threads(threads: List):
    """
    Start all provided thread objects.

    Args:
        threads: List of thread objects to start
    """
    for thread in threads:
        thread.start()


def stop_all_threads(threads: List):
    """
    Stop all threads gracefully.

    Args:
        threads: List of thread objects to stop
    """
    for thread in threads:
        if isinstance(thread, (mouse.Listener, keyboard.Listener)):
            thread.stop()
        thread.join()


def cleanup_threads(threads: List):
    """
    Perform cleanup and graceful shutdown of all threads.

    Args:
        threads: List of all active threads
    """
    logging.info("Stopping all threads...")
    stop_all_threads(threads)
    logging.info("All threads stopped successfully.")
