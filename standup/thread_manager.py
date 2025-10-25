import logging
from typing import List

from pynput import keyboard, mouse

logger = logging.getLogger(__name__)


class ThreadManager:
    """Thread lifecycle management for input listeners and workers."""

    def start_all(self, threads: List):
        """Start all provided thread objects sequentially."""
        for thread in threads:
            thread.start()

    def stop_all(self, threads: List):
        """Stop all threads gracefully and wait for completion."""
        for thread in threads:
            if self._is_input_listener(thread):
                thread.stop()
            thread.join()

    def cleanup(self, threads: List):
        """Perform cleanup and graceful shutdown of all threads."""
        logger.info("Stopping all threads...")
        self.stop_all(threads)
        logger.info("All threads stopped successfully.")

    def _is_input_listener(self, thread) -> bool:
        """Check if thread is a pynput mouse or keyboard listener."""
        return isinstance(thread, (mouse.Listener, keyboard.Listener))
