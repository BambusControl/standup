import time
import logging

from .models import AppState, AppConfig, State, state_to_activity
from . import app
from .utils import show_notification, log_to_csv, format_duration


def handle_active_state(app_state: AppState, config: AppConfig) -> AppState:
    """Manages state transitions and actions when the user is ACTIVE."""
    now = time.time()
    time_since_last_activity = now - app.last_activity_time

    # Transition: ACTIVE -> IDLE
    if time_since_last_activity >= config.break_duration_sec:
        logging.info("User inactive. Transitioning to IDLE.")
        duration = now - app_state.session_start_time

        log_to_csv(
            config,
            state_to_activity(app_state.current_state),
            app_state.session_start_time,
            now,
            duration,
        )

        return app_state._replace(
            current_state=State.IDLE,
            session_start_time=now,
            break_reminder_shown=False,
        )

    # Action: Show break reminder
    if (
        not app_state.break_reminder_shown
        and (now - app_state.session_start_time) >= config.work_duration_sec
    ):
        duration = now - app_state.session_start_time

        show_notification(
            "Time for a break!",
            f"You've been active for {format_duration(duration)}.",
            "Step away for a bit.",
        )
        logging.info("Break reminder triggered.")
        return app_state._replace(break_reminder_shown=True)

    return app_state  # No state change


def handle_idle_state(app_state: AppState, config: AppConfig) -> AppState:
    """Manages state transitions and actions when the user is IDLE."""
    now = time.time()
    time_since_last_activity = now - app.last_activity_time

    # Transition: IDLE -> ACTIVE
    if time_since_last_activity < config.break_duration_sec:
        logging.info("User active. Transitioning to ACTIVE.")
        duration = now - app_state.session_start_time

        show_notification(
            "Welcome Back!",
            f"Your break lasted {format_duration(duration)}.",
            "Starting new session.",
        )

        log_to_csv(
            config,
            state_to_activity(app_state.current_state),
            app_state.session_start_time,
            now,
            duration,
        )

        return app_state._replace(current_state=State.ACTIVE, session_start_time=now)

    return app_state  # No state change
