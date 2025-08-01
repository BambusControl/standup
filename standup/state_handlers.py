"""
State transition handlers for the activity monitoring state machine.

This module implements the state machine logic for transitioning between
ACTIVE and IDLE states based on user activity, and handles associated
actions like notifications and logging.
"""

import time
import logging

from .models import AppState, AppConfig, State, state_to_activity
from .activity_tracker import get_last_activity_time
from .utils import show_notification, log_to_csv, format_duration

# Session duration threshold for logging (in seconds)
MINIMUM_LOG_DURATION = 1


def handle_active_state(app_state: AppState, config: AppConfig) -> AppState:
    """
    Manages state transitions and actions when the user is ACTIVE.

    Handles:
    - Transition to IDLE state when user becomes inactive
    - Break reminder notifications after extended work periods

    Args:
        app_state: Current application state
        config: Application configuration

    Returns:
        Updated application state
    """
    current_time = time.time()
    time_since_last_activity = current_time - get_last_activity_time()

    # Check for transition: ACTIVE -> IDLE
    if _should_transition_to_idle(time_since_last_activity, config):
        return _transition_to_idle_state(app_state, config, current_time)

    # Check for break reminder
    if _should_show_break_reminder(app_state, config, current_time):
        return _show_break_reminder(app_state, current_time)

    return app_state  # No state change


def handle_idle_state(app_state: AppState, config: AppConfig) -> AppState:
    """
    Manages state transitions and actions when the user is IDLE.

    Handles:
    - Transition to ACTIVE state when user becomes active
    - Welcome back notifications after breaks

    Args:
        app_state: Current application state
        config: Application configuration

    Returns:
        Updated application state
    """
    current_time = time.time()
    time_since_last_activity = current_time - get_last_activity_time()

    # Stay idle if user is still inactive
    if time_since_last_activity >= config.break_duration_sec:
        return app_state

    # Transition: IDLE -> ACTIVE
    return _transition_to_active_state(app_state, config, current_time)


def _should_transition_to_idle(
    time_since_last_activity: float, config: AppConfig
) -> bool:
    """
    Determine if we should transition from ACTIVE to IDLE state.

    Args:
        time_since_last_activity: Seconds since last user activity
        config: Application configuration

    Returns:
        True if should transition to idle, False otherwise
    """
    return time_since_last_activity >= config.break_duration_sec


def _should_show_break_reminder(
    app_state: AppState, config: AppConfig, current_time: float
) -> bool:
    """
    Determine if we should show a break reminder.

    Args:
        app_state: Current application state
        config: Application configuration
        current_time: Current timestamp

    Returns:
        True if should show break reminder, False otherwise
    """
    work_duration = current_time - app_state.session_start_time
    return (
        not app_state.break_reminder_shown and work_duration >= config.work_duration_sec
    )


def _transition_to_idle_state(
    app_state: AppState, config: AppConfig, current_time: float
) -> AppState:
    """
    Handle transition from ACTIVE to IDLE state.

    Args:
        app_state: Current application state
        config: Application configuration
        current_time: Current timestamp

    Returns:
        Updated application state in IDLE mode
    """
    logging.info("User inactive. Transitioning to IDLE.")
    session_duration = current_time - app_state.session_start_time

    if session_duration > MINIMUM_LOG_DURATION:
        log_to_csv(
            config,
            state_to_activity(app_state.current_state),
            app_state.session_start_time,
            current_time,
            session_duration,
        )

    return app_state._replace(
        current_state=State.IDLE,
        session_start_time=current_time,
        break_reminder_shown=False,
    )


def _transition_to_active_state(
    app_state: AppState, config: AppConfig, current_time: float
) -> AppState:
    """
    Handle transition from IDLE to ACTIVE state.

    Args:
        app_state: Current application state
        config: Application configuration
        current_time: Current timestamp

    Returns:
        Updated application state in ACTIVE mode
    """
    logging.info("User active. Transitioning to ACTIVE.")
    break_duration = current_time - app_state.session_start_time

    if break_duration > MINIMUM_LOG_DURATION:
        show_notification(
            "Welcome Back!",
            f"Your break lasted {format_duration(break_duration)}.",
            "Starting new session.",
        )

        log_to_csv(
            config,
            state_to_activity(app_state.current_state),
            app_state.session_start_time,
            current_time,
            break_duration,
        )

    return app_state._replace(
        current_state=State.ACTIVE, session_start_time=current_time
    )


def _show_break_reminder(app_state: AppState, current_time: float) -> AppState:
    """
    Show break reminder notification and update state.

    Args:
        app_state: Current application state
        current_time: Current timestamp

    Returns:
        Updated application state with break reminder shown
    """
    work_duration = current_time - app_state.session_start_time

    show_notification(
        "Time for a break!",
        f"You've been active for {format_duration(work_duration)}.",
        "Step away for a bit.",
    )
    logging.info("Break reminder triggered.")
    return app_state._replace(break_reminder_shown=True)
