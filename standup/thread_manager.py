"""
Thread lifecycle management for the activity monitoring system.

This module provides utilities for managing the lifecycle of all threads
used in the application, including starting, stopping, and cleanup.
"""

import logging
from typing import List

from pynput import keyboard, mouse

# Set up module-level logger
logger = logging.getLogger(__name__)


def start_all_threads(threads: List):
    """
    Start all provided thread objects sequentially.

    Args:
        threads: List of thread objects to start
    """
    for thread in threads:
        thread.start()


def _is_input_listener(thread) -> bool:
    """
    Check if a thread is an input listener (mouse or keyboard).

    Args:
        thread: Thread object to check

    Returns:
        True if thread is an input listener, False otherwise
    """
    return isinstance(thread, (mouse.Listener, keyboard.Listener))


def stop_all_threads(threads: List):
    """
    Stop all threads gracefully and wait for completion.

    Args:
        threads: List of thread objects to stop
    """
    for thread in threads:
        if _is_input_listener(thread):
            thread.stop()
        thread.join()


def cleanup_threads(threads: List):
    """
    Perform cleanup and graceful shutdown of all threads.

    Args:
        threads: List of all active threads
    """
    logger.info("Stopping all threads...")
    stop_all_threads(threads)
    logger.info("All threads stopped successfully.")
