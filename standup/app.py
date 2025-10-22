"""
Main application module for the activity monitoring system.

This module orchestrates the entire activity monitoring application, focusing
on high-level coordination and the main application loop.
"""

import logging
import time
import signal
import atexit
import sys

from pynput import keyboard, mouse

from .activity_tracker import on_activity, set_last_activity_time
from .data_collector import (
    COLLECTION_INTERVAL_SECONDS,
    start_data_collection,
    stop_data_collection,
)
from .models import AppConfig, AppState, State, state_to_activity
from .state_handlers import handle_active_state, handle_idle_state
from .thread_manager import cleanup_threads, start_all_threads
from .utils import log_to_csv, save_runtime_state, load_runtime_state

# Set up module-level logger
logger = logging.getLogger(__name__)

# Configuration constants
TEST_MODE_DURATION_MULTIPLIER = 3
TEST_MODE_BUFFER_SECONDS = 1
MINIMUM_SESSION_DURATION_SECONDS = 1
DEFAULT_ENCODING = "utf-8"


def run_app(config: AppConfig):
    """
    Main application entry point that runs the activity monitoring state machine.

    Initializes all necessary components:
    - Application state
    - Input listeners for state machine
    - Raw data collection system
    - Background threads

    Args:
        config: Application configuration settings
    """
    app_state = _initialize_app_state()
    # Try to load previously saved runtime state and resume from it
    try:
        saved = load_runtime_state(config)
        if saved:
            # Map the saved state into a new AppState, keeping monotonic timestamps fresh
            saved_state_name = saved.get("current_state")
            try:
                saved_state = State[saved_state_name]
            except Exception:
                saved_state = app_state.current_state

            saved_session_start = float(
                saved.get("session_start_time", app_state.session_start_time)
            )
            saved_break_reminder = bool(saved.get("break_reminder_shown", False))

            app_state = app_state._replace(
                current_state=saved_state,
                session_start_time=saved_session_start,
                session_start_monotonic=time.monotonic(),
                activation_candidate_start_monotonic=None,
                break_reminder_shown=saved_break_reminder,
            )
            # Restore last activity wall-clock time; monotonic will be reset to now
            try:
                set_last_activity_time(
                    float(saved.get("last_activity_time", app_state.session_start_time))
                )
            except Exception:
                logger.exception("Failed to set last activity time from saved state")
            logger.info("Resumed state from saved runtime state: %s", saved)
    except Exception:
        logger.exception("Failed to load saved runtime state")
    # Set both wall-clock and monotonic last-activity timestamps
    set_last_activity_time(
        app_state.session_start_time, app_state.session_start_monotonic
    )

    config = _configure_for_test_mode(config)
    logger.info("--- Activity Monitor Started (Config: %s) ---", config)

    all_threads = _setup_monitoring_system(config)
    start_all_threads(all_threads)

    # Register signal handlers to save state on termination
    def _save_state_and_exit(signum=None, frame=None):
        logger.info("Received signal %s - saving runtime state and exiting", signum)
        try:
            from .activity_tracker import get_last_activity_time

            save_runtime_state(config, app_state, get_last_activity_time())
        except Exception:
            logger.exception("Failed to save runtime state in signal handler")
        try:
            # Attempt a graceful exit
            sys.exit(0)
        except SystemExit:
            # Re-raise to allow normal exit
            raise

    # SIGINT (Ctrl+C) is always available; SIGTERM may not exist on Windows but try to register
    try:
        signal.signal(signal.SIGINT, _save_state_and_exit)
    except Exception:
        logger.exception("Failed to register SIGINT handler")
    try:
        signal.signal(signal.SIGTERM, _save_state_and_exit)
    except Exception:
        # SIGTERM may not be available on some platforms; ignore if so
        logger.debug("SIGTERM not available on this platform")

    # Also register an atexit handler to persist state on normal exit
    def _on_exit():
        try:
            from .activity_tracker import get_last_activity_time

            save_runtime_state(config, app_state, get_last_activity_time())
        except Exception:
            logger.exception("Failed to save runtime state in atexit handler")

    atexit.register(_on_exit)

    # The main loop modifies the app state, so we need to update it before shutdown
    if config.test_mode:
        app_state = _run_main_test_loop(app_state, config)
    else:
        app_state = _run_main_loop(app_state, config)

    _cleanup_and_shutdown(app_state, config, all_threads)


def _initialize_app_state() -> AppState:
    """
    Initialize the application state.

    Returns:
        Initial AppState with IDLE state and current timestamp
    """
    return AppState(
        current_state=State.IDLE,
        session_start_time=time.time(),
        session_start_monotonic=time.monotonic(),
        activation_candidate_start_monotonic=None,
        break_reminder_shown=False,
    )


def _configure_for_test_mode(config: AppConfig) -> AppConfig:
    """
    Configure the application for test mode if enabled.

    Args:
        config: Original configuration

    Returns:
        Modified configuration for test mode, or original if not test mode
    """
    if not config.test_mode:
        return config

    logger.info("--- Test mode ---")
    test_csv_file = config.csv_file.with_stem(f"test_{config.csv_file.stem}")
    return config._replace(csv_file=test_csv_file)


def _setup_monitoring_system(config: AppConfig) -> list:
    """
    Set up all monitoring threads and listeners.

    Args:
        config: Application configuration

    Returns:
        List of all thread objects that need to be started
    """
    all_threads = []

    # Create state machine listeners
    state_machine_listeners = _create_state_machine_listeners()
    all_threads.extend(state_machine_listeners)

    # Create data collection system
    raw_data_filename = config.csv_file.with_stem(f"{config.csv_file.stem}_raw")

    if config.test_mode:
        # Empty the file before starting during tests
        raw_data_filename.write_text("", encoding=DEFAULT_ENCODING)

    data_collector_threads = start_data_collection(raw_data_filename)
    all_threads.extend(data_collector_threads)

    return all_threads


def _create_state_machine_listeners() -> list:
    """
    Create input listeners for the state machine.

    Returns:
        List of listener objects for mouse and keyboard
    """
    mouse_listener = mouse.Listener(
        on_move=on_activity, on_click=on_activity, on_scroll=on_activity
    )
    keyboard_listener = keyboard.Listener(on_press=on_activity)

    return [mouse_listener, keyboard_listener]


def _run_main_loop(app_state: AppState, config: AppConfig) -> AppState:
    """
    Run the main application loop with state machine processing.

    Args:
        app_state: Current application state
        config: Application configuration
    """
    try:
        while True:
            app_state = _process_current_state(app_state, config)
            time.sleep(COLLECTION_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("--- KeyboardInterrupt detected. Quitting ---")
    finally:
        return app_state


def _run_main_test_loop(app_state: AppState, config: AppConfig) -> AppState:
    """
    Run the main application loop for testing purposes.

    Args:
        app_state: Current application state
        config: Application configuration
    """
    start_time = time.time()

    while not _should_exit_test_mode(start_time):
        app_state = _process_current_state(app_state, config)
        time.sleep(COLLECTION_INTERVAL_SECONDS)
    return app_state


def _should_exit_test_mode(start_time: float) -> bool:
    """
    Check if we should exit due to test mode duration limit.

    Args:
        config: Application configuration
        start_time: When the application started

    Returns:
        True if should exit, False otherwise
    """
    test_duration = (
        COLLECTION_INTERVAL_SECONDS * TEST_MODE_DURATION_MULTIPLIER
        + TEST_MODE_BUFFER_SECONDS
    )
    elapsed_time = time.time() - start_time

    if elapsed_time >= test_duration:
        logger.info("--- Test mode: Exiting after %s seconds. ---", test_duration)
        return True
    return False


def _process_current_state(app_state: AppState, config: AppConfig) -> AppState:
    """
    Process the current state and return updated state.

    Args:
        app_state: Current application state
        config: Application configuration

    Returns:
        Updated application state
    """
    if app_state.current_state == State.ACTIVE:
        return handle_active_state(app_state, config)
    elif app_state.current_state == State.IDLE:
        return handle_idle_state(app_state, config)

    return app_state


def _cleanup_and_shutdown(app_state: AppState, config: AppConfig, all_threads: list):
    """
    Perform cleanup and graceful shutdown of all components.

    Args:
        app_state: Final application state
        config: Application configuration
        all_threads: List of all active threads
    """
    logger.info("Shutting down. Saving final session.")

    _log_final_session(app_state, config)
    # Persist the runtime state so next startup can resume accurately
    try:
        from .activity_tracker import get_last_activity_time

        save_runtime_state(config, app_state, get_last_activity_time())
    except Exception:
        logger.exception("Failed to save runtime state during cleanup")
    stop_data_collection()
    cleanup_threads(all_threads)

    logger.info("Listeners stopped. Exiting.")


def _log_final_session(app_state: AppState, config: AppConfig):
    """
    Log the final session if it meets duration requirements.

    Args:
        app_state: Final application state
        config: Application configuration
    """
    final_time = time.time()
    # Prefer monotonic-based duration to avoid issues from clock adjustments
    try:
        session_duration = time.monotonic() - app_state.session_start_monotonic
    except Exception:
        session_duration = final_time - app_state.session_start_time

    if session_duration > MINIMUM_SESSION_DURATION_SECONDS:
        log_to_csv(
            config,
            state_to_activity(app_state.current_state),
            app_state.session_start_time,
            final_time,
            session_duration,
        )
