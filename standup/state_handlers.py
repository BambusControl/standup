"""
State transition handlers for the activity monitoring state machine.

This module implements the state machine logic for transitioning between
ACTIVE and IDLE states based on user activity, and handles associated
actions like notifications and logging.
"""

import logging
import time
import math

from .activity_tracker import get_last_activity_time, get_last_activity_monotonic
from .models import AppConfig, AppState, State, state_to_activity
from .utils import format_duration, log_to_csv, show_notification

# Set up module-level logger
logger = logging.getLogger(__name__)

# Duration threshold constants (in seconds)
MINIMUM_LOG_DURATION_SECONDS = 1
SLEEP_DETECTION_THRESHOLD_SECONDS = 60
# Activation candidate requires frequent events; we consider activity
# broken if the gap between events exceeds activation_threshold_sec / GAP_DIVISOR
ACTIVATION_GAP_DIVISOR = 10


def _calculate_time_since_activity() -> float:
    """
    Calculate time elapsed since last user activity.

    Returns:
        Seconds since last activity
    """
    now_wall = time.time()
    now_mono = time.monotonic()
    try:
        last_wall = get_last_activity_time()
        last_mono = get_last_activity_monotonic()
        delta_wall = now_wall - last_wall
        delta_mono = now_mono - last_mono
        # If wall-clock shows a much larger gap than monotonic, assume
        # system suspend/wake occurred and use the wall-clock duration.
        if delta_wall - delta_mono > SLEEP_DETECTION_THRESHOLD_SECONDS:
            return delta_wall
        return delta_mono
    except Exception:
        return now_wall - get_last_activity_time()


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
    current_monotonic = time.monotonic()
    time_since_last_activity = _calculate_time_since_activity()

    # Check for transition: ACTIVE -> IDLE
    if _should_transition_to_idle(time_since_last_activity, config):
        return _transition_to_idle_state(
            app_state, config, current_time, current_monotonic
        )

    # Check for break reminder
    if _should_show_break_reminder(app_state, config, current_time, current_monotonic):
        return _show_break_reminder(app_state, current_time, current_monotonic)

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
    current_monotonic = time.monotonic()
    time_since_last_activity = _calculate_time_since_activity()

    # Stay idle if user is still inactive. Also reset candidate if events are too sparse
    # to count as sustained activity. For example, for a 10s activation threshold,
    # we require at least one event per second (10s / 10).
    max_inter_event_gap = config.activation_threshold_sec / ACTIVATION_GAP_DIVISOR
    if (
        time_since_last_activity >= config.break_duration_sec
        or time_since_last_activity >= max_inter_event_gap
    ):
        # Reset any in-progress activation candidate
        if app_state.activation_candidate_start_monotonic is not None:
            return app_state._replace(activation_candidate_start_monotonic=None)
        return app_state

    # Some activity was detected within the break window. Require sustained
    # activity (activation threshold) before switching to ACTIVE.
    candidate = app_state.activation_candidate_start_monotonic
    if candidate is None:
        # Start candidate timer
        return app_state._replace(
            activation_candidate_start_monotonic=current_monotonic
        )

    # Check if sustained activity meets threshold
    if current_monotonic - candidate >= config.activation_threshold_sec:
        return _transition_to_active_state(
            app_state, config, current_time, current_monotonic
        )

    # Not yet sustained enough; remain in IDLE with candidate
    return app_state


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


def _calculate_session_duration(
    app_state: AppState, current_time: float, current_monotonic: float
) -> float:
    """
    Calculate the duration of the current session.

    Args:
        app_state: Current application state
        current_time: Current timestamp

    Returns:
        Session duration in seconds
    """
    try:
        delta_mono = current_monotonic - app_state.session_start_monotonic
    except Exception:
        delta_mono = None

    delta_wall = current_time - app_state.session_start_time

    if delta_mono is None:
        return delta_wall

    # If wall clock shows a much larger gap (suspend), prefer wall-clock
    if delta_wall - delta_mono > SLEEP_DETECTION_THRESHOLD_SECONDS:
        return delta_wall

    return delta_mono


def _should_show_break_reminder(
    app_state: AppState,
    config: AppConfig,
    current_time: float,
    current_monotonic: float,
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
    work_duration = _calculate_session_duration(
        app_state, current_time, current_monotonic
    )
    return (
        not app_state.break_reminder_shown and work_duration >= config.work_duration_sec
    )


def _should_log_session(session_duration: float) -> bool:
    """
    Determine if a session should be logged based on its duration.

    Args:
        session_duration: Duration of the session in seconds

    Returns:
        True if session should be logged, False otherwise
    """
    return session_duration > MINIMUM_LOG_DURATION_SECONDS


def _transition_to_idle_state(
    app_state: AppState,
    config: AppConfig,
    current_time: float,
    current_monotonic: float,
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
    logger.info("User inactive. Transitioning to IDLE.")
    session_duration = _calculate_session_duration(
        app_state, current_time, current_monotonic
    )

    if _should_log_session(session_duration):
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
        session_start_monotonic=current_monotonic,
        activation_candidate_start_monotonic=None,
        break_reminder_shown=False,
    )


def _transition_to_active_state(
    app_state: AppState,
    config: AppConfig,
    current_time: float,
    current_monotonic: float,
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
    logger.info("User active. Transitioning to ACTIVE.")
    break_duration = _calculate_session_duration(
        app_state, current_time, current_monotonic
    )

    if _should_log_session(break_duration):
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
        current_state=State.ACTIVE,
        session_start_time=current_time,
        session_start_monotonic=current_monotonic,
        activation_candidate_start_monotonic=None,
    )


def _show_break_reminder(
    app_state: AppState, current_time: float, current_monotonic: float
) -> AppState:
    """
    Show break reminder notification and update state.

    Args:
        app_state: Current application state
        current_time: Current timestamp

    Returns:
        Updated application state with break reminder shown
    """
    session_duration_seconds = _calculate_session_duration(
        app_state, current_time, current_monotonic
    )
    pushups_per_minute = 1 / 10  # 1 pushup every 10 minutes
    pushups_per_second = pushups_per_minute / 60
    pushups_to_do = math.ceil(session_duration_seconds * pushups_per_second)

    show_notification(
        "Time for a break!",
        f"You've been active for {format_duration(session_duration_seconds)}.",
        f"Now your goal is to do {pushups_to_do} pushups!",
    )
    logger.info("Break reminder triggered.")
    return app_state._replace(break_reminder_shown=True)
