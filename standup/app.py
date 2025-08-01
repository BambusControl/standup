import time
import logging

from pynput import mouse, keyboard

from .models import AppState, AppConfig, State, state_to_activity
from .state_handlers import handle_active_state, handle_idle_state
from .utils import show_notification, log_to_csv
from .data_collector import (
    start_data_collection,
    stop_data_collection,
    COLLECTION_INTERVAL_SECONDS,
)

# --- Global State for Listeners ---
last_activity_time = time.time()


def on_activity(x=None, y=None, button=None, pressed=None, key=None):
    """Callback for listeners. Updates the global last activity time."""
    global last_activity_time
    last_activity_time = time.time()


def run_app(config: AppConfig):
    """Main function to run the activity monitoring state machine."""
    global last_activity_time

    app_state = AppState(
        current_state=State.IDLE,
        session_start_time=time.time(),
        break_reminder_shown=False,
    )
    last_activity_time = app_state.session_start_time

    if config.test_mode:
        logging.info("--- Test mode ---")
        config = config._replace(
            csv_file=config.csv_file.with_stem("test_" + config.csv_file.stem)
        )

    logging.info(f"--- Activity Monitor Started (Config: {config}) ---")
    show_notification(
        "Activity Monitor Started",
        "Monitoring your computer usage.",
        f"Logs will be saved to {config.csv_file}",
    )

    # All threads that need to be started
    all_threads = []

    # Main state-machine listeners
    mouse_listener_sm = mouse.Listener(
        on_move=on_activity, on_click=on_activity, on_scroll=on_activity
    )
    keyboard_listener_sm = keyboard.Listener(on_press=on_activity)
    all_threads.extend([mouse_listener_sm, keyboard_listener_sm])

    # Data collection listeners and poller
    data_collector_listeners = start_data_collection(
        config.csv_file.with_stem(config.csv_file.stem + "_raw")
    )
    all_threads.extend(data_collector_listeners)

    for thread in all_threads:
        thread.start()

    last_state_before_quitting = None
    start_time = time.time()

    try:
        while app_state.current_state != State.QUITTING:
            test_duration = COLLECTION_INTERVAL_SECONDS * 3 + 1

            if config.test_mode and (time.time() - start_time) >= test_duration:
                logging.info(
                    f"--- Test mode: Exiting after {test_duration} seconds. ---"
                )
                break

            if app_state.current_state == State.ACTIVE:
                app_state = handle_active_state(app_state, config)
            elif app_state.current_state == State.IDLE:
                app_state = handle_idle_state(app_state, config)

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("--- KeyboardInterrupt detected. Transitioning to QUITTING. ---")
        last_state_before_quitting = app_state.current_state
        app_state = app_state._replace(current_state=State.QUITTING)

    finally:
        logging.info("Shutting down. Saving final session.")
        final_time = time.time()

        if last_state_before_quitting:
            duration = final_time - app_state.session_start_time
            if duration > 1:
                log_to_csv(
                    config,
                    state_to_activity(last_state_before_quitting),
                    app_state.session_start_time,
                    final_time,
                    duration,
                )

        stop_data_collection()  # Signal the data collector to stop its polling thread

        for thread in all_threads:
            if isinstance(thread, (mouse.Listener, keyboard.Listener)):
                thread.stop()
            thread.join()

        logging.info("Listeners stopped. Exiting.")
