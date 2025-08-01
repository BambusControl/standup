"""
Main application module for the activity monitoring system.

This module orchestrates the entire activity monitoring application, focusing
on high-level coordination and the main application loop.
"""

import time
import logging

from pynput import mouse, keyboard

from .models import AppState, AppConfig, State, state_to_activity
from .state_handlers import handle_active_state, handle_idle_state
from .utils import log_to_csv
from .data_collector import (
    start_data_collection,
    stop_data_collection,
    COLLECTION_INTERVAL_SECONDS,
)
from .activity_tracker import on_activity, set_last_activity_time
from .thread_manager import start_all_threads, cleanup_threads

# Configuration constants
TEST_MODE_DURATION_MULTIPLIER = 3
TEST_MODE_BUFFER_SECONDS = 1
MINIMUM_SESSION_DURATION = 1


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
    set_last_activity_time(app_state.session_start_time)

    config = _configure_for_test_mode(config)
    logging.info(f"--- Activity Monitor Started (Config: {config}) ---")

    all_threads = _setup_monitoring_system(config)
    start_all_threads(all_threads)

    try:
        _run_main_loop(app_state, config)
    except KeyboardInterrupt:
        logging.info("--- KeyboardInterrupt detected. Quitting ---")
    finally:
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

    logging.info("--- Test mode ---")
    test_csv_file = config.csv_file.with_stem("test_" + config.csv_file.stem)
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
    raw_data_filename = config.csv_file.with_stem(config.csv_file.stem + "_raw")
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


def _run_main_loop(app_state: AppState, config: AppConfig):
    """
    Run the main application loop with state machine processing.

    Args:
        app_state: Current application state
        config: Application configuration
    """
    start_time = time.time()

    while True:
        if _should_exit_test_mode(config, start_time):
            break

        app_state = _process_current_state(app_state, config)
        time.sleep(COLLECTION_INTERVAL_SECONDS)


def _should_exit_test_mode(config: AppConfig, start_time: float) -> bool:
    """
    Check if we should exit due to test mode duration limit.

    Args:
        config: Application configuration
        start_time: When the application started

    Returns:
        True if should exit, False otherwise
    """
    if not config.test_mode:
        return False

    test_duration = (
        COLLECTION_INTERVAL_SECONDS * TEST_MODE_DURATION_MULTIPLIER
        + TEST_MODE_BUFFER_SECONDS
    )
    elapsed_time = time.time() - start_time

    if elapsed_time >= test_duration:
        logging.info(f"--- Test mode: Exiting after {test_duration} seconds. ---")
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
    logging.info("Shutting down. Saving final session.")

    _log_final_session(app_state, config)
    stop_data_collection()
    cleanup_threads(all_threads)

    logging.info("Listeners stopped. Exiting.")


def _log_final_session(app_state: AppState, config: AppConfig):
    """
    Log the final session if it meets duration requirements.

    Args:
        app_state: Final application state
        config: Application configuration
    """
    final_time = time.time()
    session_duration = final_time - app_state.session_start_time

    if session_duration > MINIMUM_SESSION_DURATION:
        log_to_csv(
            config,
            state_to_activity(app_state.current_state),
            app_state.session_start_time,
            final_time,
            session_duration,
        )
