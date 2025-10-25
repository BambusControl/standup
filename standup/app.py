"""Main application orchestration and lifecycle management."""

import logging
import time
import signal
import atexit
import sys

from pynput import keyboard, mouse

from .activity_tracker import ActivityTracker
from .constants import COLLECTION_INTERVAL_SECONDS
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
    """Main entry point: initialize components and run the state machine."""
    activity_tracker = ActivityTracker()
    app_state = _initialize_app_state()
    # Try to load previously saved runtime state and resume from it
    resumed_from_saved_state = False
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
            saved_last_activity = float(saved.get("last_activity_time", time.time()))

            current_time = time.time()
            current_monotonic = time.monotonic()

            # Simulate missing time: check if inactivity threshold was exceeded during downtime
            time_since_last_activity = current_time - saved_last_activity

            # If we were ACTIVE and the downtime exceeded the inactivity threshold,
            # we need to simulate the state transition that should have occurred
            if (
                saved_state == State.ACTIVE
                and time_since_last_activity >= config.break_duration_sec
            ):
                # The active session should have ended at last_activity + inactivity_threshold
                active_session_end = saved_last_activity + config.break_duration_sec
                active_session_duration = active_session_end - saved_session_start

                # Log the active session that ended during downtime
                if active_session_duration > MINIMUM_SESSION_DURATION_SECONDS:
                    logger.info(
                        "Simulating missed ACTIVE->IDLE transition during downtime. "
                        "Active session ended at %s (duration: %.1fs)",
                        active_session_end,
                        active_session_duration,
                    )
                    log_to_csv(
                        config,
                        state_to_activity(State.ACTIVE),
                        saved_session_start,
                        active_session_end,
                        active_session_duration,
                    )

                # Now we've been in IDLE (break) since then
                break_duration = current_time - active_session_end

                # Show welcome back notification with actual break duration
                from .utils import show_notification, format_duration

                show_notification(
                    "Welcome Back!",
                    f"Your break lasted {format_duration(break_duration)}.",
                    "Starting new session.",
                )

                # Start fresh in IDLE state with the corrected session start time
                app_state = app_state._replace(
                    current_state=State.IDLE,
                    session_start_time=active_session_end,
                    session_start_monotonic=current_monotonic,
                    activation_candidate_start_monotonic=None,
                    break_reminder_shown=False,
                )
                # Set last activity to the saved value, not current time
                activity_tracker.set_last_activity_time(
                    saved_last_activity, current_monotonic
                )
            else:
                # Normal resume: no state transition needed
                app_state = app_state._replace(
                    current_state=saved_state,
                    session_start_time=saved_session_start,
                    session_start_monotonic=current_monotonic,
                    activation_candidate_start_monotonic=None,
                    break_reminder_shown=saved_break_reminder,
                )
                # Set last activity time to current time for seamless continuation
                activity_tracker.set_last_activity_time(current_time, current_monotonic)

            resumed_from_saved_state = True
            logger.info("Resumed state from saved runtime state: %s", saved)
    except Exception:
        logger.exception("Failed to load saved runtime state")

    # Only set initial activity timestamp if we're starting fresh (not resuming)
    if not resumed_from_saved_state:
        activity_tracker.set_last_activity_time(
            app_state.session_start_time, app_state.session_start_monotonic
        )

    config = _configure_for_test_mode(config)
    logger.info("--- Activity Monitor Started (Config: %s) ---", config)

    all_threads = _setup_monitoring_system(config, activity_tracker)
    start_all_threads(all_threads)

    # Register signal handlers to save state on termination
    def _save_state_and_exit(signum=None, frame=None):
        logger.info("Received signal %s - saving runtime state and exiting", signum)
        try:
            save_runtime_state(
                config, app_state, activity_tracker.get_last_activity_time()
            )
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
            save_runtime_state(
                config, app_state, activity_tracker.get_last_activity_time()
            )
        except Exception:
            logger.exception("Failed to save runtime state in atexit handler")

    atexit.register(_on_exit)

    # The main loop modifies the app state, so we need to update it before shutdown
    if config.test_mode:
        app_state = _run_main_test_loop(app_state, config, activity_tracker)
    else:
        app_state = _run_main_loop(app_state, config, activity_tracker)

    _cleanup_and_shutdown(app_state, config, all_threads, activity_tracker)


def _initialize_app_state() -> AppState:
    """Return initial IDLE state with current timestamps."""
    return AppState(
        current_state=State.IDLE,
        session_start_time=time.time(),
        session_start_monotonic=time.monotonic(),
        activation_candidate_start_monotonic=None,
        break_reminder_shown=False,
    )


def _configure_for_test_mode(config: AppConfig) -> AppConfig:
    """Modify config for test mode or return unchanged."""
    if not config.test_mode:
        return config

    logger.info("--- Test mode ---")
    test_csv_file = config.csv_file.with_stem(f"test_{config.csv_file.stem}")
    return config._replace(csv_file=test_csv_file)


def _setup_monitoring_system(
    config: AppConfig, activity_tracker: ActivityTracker
) -> list:
    """Create and return all monitoring threads and listeners."""
    all_threads = []

    # Create state machine listeners
    state_machine_listeners = _create_state_machine_listeners(activity_tracker)
    all_threads.extend(state_machine_listeners)

    # No window monitoring system (removed)

    return all_threads


def _create_state_machine_listeners(activity_tracker: ActivityTracker) -> list:
    """Create mouse and keyboard input listeners."""
    mouse_listener = mouse.Listener(
        on_move=activity_tracker.on_activity,
        on_click=activity_tracker.on_activity,
        on_scroll=activity_tracker.on_activity,
    )
    keyboard_listener = keyboard.Listener(on_press=activity_tracker.on_activity)

    return [mouse_listener, keyboard_listener]


def _run_main_loop(
    app_state: AppState, config: AppConfig, activity_tracker: ActivityTracker
) -> AppState:
    """Run main state machine loop until interrupted."""
    try:
        while True:
            app_state = _process_current_state(app_state, config, activity_tracker)
            time.sleep(COLLECTION_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("--- KeyboardInterrupt detected. Quitting ---")
    finally:
        return app_state


def _run_main_test_loop(
    app_state: AppState, config: AppConfig, activity_tracker: ActivityTracker
) -> AppState:
    """Run state machine loop for limited test duration."""
    start_time = time.time()

    while not _should_exit_test_mode(start_time):
        app_state = _process_current_state(app_state, config, activity_tracker)
        time.sleep(COLLECTION_INTERVAL_SECONDS)
    return app_state


def _should_exit_test_mode(start_time: float) -> bool:
    """Check if test mode duration limit reached."""
    test_duration = (
        COLLECTION_INTERVAL_SECONDS * TEST_MODE_DURATION_MULTIPLIER
        + TEST_MODE_BUFFER_SECONDS
    )
    elapsed_time = time.time() - start_time

    if elapsed_time >= test_duration:
        logger.info("--- Test mode: Exiting after %s seconds. ---", test_duration)
        return True
    return False


def _process_current_state(
    app_state: AppState, config: AppConfig, activity_tracker: ActivityTracker
) -> AppState:
    """Process current state and return updated state."""
    if app_state.current_state == State.ACTIVE:
        return handle_active_state(app_state, config, activity_tracker)
    elif app_state.current_state == State.IDLE:
        return handle_idle_state(app_state, config, activity_tracker)

    return app_state


def _cleanup_and_shutdown(
    app_state: AppState,
    config: AppConfig,
    all_threads: list,
    activity_tracker: ActivityTracker,
):
    """Cleanup and graceful shutdown of all components."""
    logger.info("Shutting down. Saving final session.")

    _log_final_session(app_state, config)
    # Persist the runtime state so next startup can resume accurately
    try:
        save_runtime_state(config, app_state, activity_tracker.get_last_activity_time())
    except Exception:
        logger.exception("Failed to save runtime state during cleanup")
    cleanup_threads(all_threads)

    logger.info("Listeners stopped. Exiting.")


def _log_final_session(app_state: AppState, config: AppConfig):
    """Log final session if duration meets minimum threshold."""
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
