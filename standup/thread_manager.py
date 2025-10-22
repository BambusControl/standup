"""Thread lifecycle management for input listeners and workers."""

import logging
from typing import List

from pynput import keyboard, mouse

# Set up module-level logger
logger = logging.getLogger(__name__)


def start_all_threads(threads: List):
    """Start all provided thread objects sequentially."""
    for thread in threads:
        thread.start()


def _is_input_listener(thread) -> bool:
    """Check if thread is a pynput mouse or keyboard listener."""
    return isinstance(thread, (mouse.Listener, keyboard.Listener))


def stop_all_threads(threads: List):
    """Stop all threads gracefully and wait for completion."""
    for thread in threads:
        if _is_input_listener(thread):
            thread.stop()
        thread.join()


def cleanup_threads(threads: List):
    """Perform cleanup and graceful shutdown of all threads."""
    logger.info("Stopping all threads...")
    stop_all_threads(threads)
    logger.info("All threads stopped successfully.")
