import logging
import time
import math

from .activity_tracker import ActivityTracker
from .model.app_config import AppConfig
from .model.app_state import AppState
from .model.state import State, state_to_activity
from .notifier import Notifier
from .session_logger import SessionLogger
from .utils import format_duration

logger = logging.getLogger(__name__)


class StateHandler:
    """State machine handlers for IDLE ↔ ACTIVE transitions and break reminders."""

    MINIMUM_LOG_DURATION_SECONDS = 1
    SLEEP_DETECTION_THRESHOLD_SECONDS = 60
    ACTIVATION_GAP_DIVISOR = 10

    def __init__(
        self,
        activity_tracker: ActivityTracker,
        session_logger: SessionLogger,
        notifier: Notifier,
    ):
        """Initialize with activity tracker, session logger, and notifier instances."""
        self._activity_tracker = activity_tracker
        self._session_logger = session_logger
        self._notifier = notifier

    def handle_active_state(self, app_state: AppState, config: AppConfig) -> AppState:
        """Handle ACTIVE state: check for IDLE transition and break reminders."""
        current_time = time.time()
        current_monotonic = time.monotonic()
        time_since_last_activity = self._calculate_time_since_activity()

        if self._should_transition_to_idle(time_since_last_activity, config):
            return self._transition_to_idle_state(
                app_state, config, current_time, current_monotonic
            )

        if self._should_show_break_reminder(
            app_state, config, current_time, current_monotonic
        ):
            return self._show_break_reminder(app_state, current_time, current_monotonic)

        return app_state

    def handle_idle_state(self, app_state: AppState, config: AppConfig) -> AppState:
        """Handle IDLE state: check for ACTIVE transition with sustained activity."""
        current_time = time.time()
        current_monotonic = time.monotonic()
        time_since_last_activity = self._calculate_time_since_activity()

        max_inter_event_gap = (
            config.activation_threshold_sec / self.ACTIVATION_GAP_DIVISOR
        )
        if (
            time_since_last_activity >= config.break_duration_sec
            or time_since_last_activity >= max_inter_event_gap
        ):
            if app_state.activation_candidate_start_monotonic is not None:
                return app_state._replace(activation_candidate_start_monotonic=None)
            return app_state

        candidate = app_state.activation_candidate_start_monotonic
        if candidate is None:
            return app_state._replace(
                activation_candidate_start_monotonic=current_monotonic
            )

        if current_monotonic - candidate >= config.activation_threshold_sec:
            return self._transition_to_active_state(
                app_state, config, current_time, current_monotonic
            )

        return app_state

    def _calculate_time_since_activity(self) -> float:
        """Calculate seconds elapsed since last user activity."""
        now_wall = time.time()
        now_mono = time.monotonic()
        try:
            last_wall = self._activity_tracker.get_last_activity_time()
            last_mono = self._activity_tracker.get_last_activity_monotonic()
            delta_wall = now_wall - last_wall
            delta_mono = now_mono - last_mono
            if delta_wall - delta_mono > self.SLEEP_DETECTION_THRESHOLD_SECONDS:
                return delta_wall
            return delta_mono
        except Exception:
            return now_wall - self._activity_tracker.get_last_activity_time()

    def _should_transition_to_idle(
        self, time_since_last_activity: float, config: AppConfig
    ) -> bool:
        """Check if inactivity duration exceeds break threshold."""
        return time_since_last_activity >= config.break_duration_sec

    def _calculate_session_duration(
        self, app_state: AppState, current_time: float, current_monotonic: float
    ) -> float:
        """Calculate current session duration handling system sleep/wake."""
        try:
            delta_mono = current_monotonic - app_state.session_start_monotonic
        except Exception:
            delta_mono = None

        delta_wall = current_time - app_state.session_start_time

        if delta_mono is None:
            return delta_wall

        if delta_wall - delta_mono > self.SLEEP_DETECTION_THRESHOLD_SECONDS:
            return delta_wall

        return delta_mono

    def _should_show_break_reminder(
        self,
        app_state: AppState,
        config: AppConfig,
        current_time: float,
        current_monotonic: float,
    ) -> bool:
        """Check if work duration exceeds threshold and reminder not yet shown."""
        work_duration = self._calculate_session_duration(
            app_state, current_time, current_monotonic
        )
        return (
            not app_state.break_reminder_shown
            and work_duration >= config.work_duration_sec
        )

    def _should_log_session(self, session_duration: float) -> bool:
        """Check if session duration exceeds minimum logging threshold."""
        return session_duration > self.MINIMUM_LOG_DURATION_SECONDS

    def _transition_to_idle_state(
        self,
        app_state: AppState,
        config: AppConfig,
        current_time: float,
        current_monotonic: float,
    ) -> AppState:
        """Transition from ACTIVE to IDLE: log session and reset state."""
        logger.info("User inactive. Transitioning to IDLE.")
        session_duration = self._calculate_session_duration(
            app_state, current_time, current_monotonic
        )

        if self._should_log_session(session_duration):
            self._session_logger.log(
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
        self,
        app_state: AppState,
        config: AppConfig,
        current_time: float,
        current_monotonic: float,
    ) -> AppState:
        """Transition from IDLE to ACTIVE: log break, show notification."""
        logger.info("User active. Transitioning to ACTIVE.")
        break_duration = self._calculate_session_duration(
            app_state, current_time, current_monotonic
        )

        if self._should_log_session(break_duration):
            self._notifier.show(
                "Welcome Back!",
                f"Your break lasted {format_duration(break_duration)}.",
                "Starting new session.",
            )

            self._session_logger.log(
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
        self, app_state: AppState, current_time: float, current_monotonic: float
    ) -> AppState:
        """Show gamified break notification with pushup challenge."""
        session_duration_seconds = self._calculate_session_duration(
            app_state, current_time, current_monotonic
        )
        pushups_per_minute = 1 / 10
        pushups_per_second = pushups_per_minute / 60
        pushups_to_do = math.ceil(session_duration_seconds * pushups_per_second)

        self._notifier.show(
            "Time for a break!",
            f"You've been active for {format_duration(session_duration_seconds)}.",
            f"Now your goal is to do {pushups_to_do} pushups!",
        )
        logger.info("Break reminder triggered.")
        return app_state._replace(break_reminder_shown=True)
