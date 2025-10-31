"""Main application orchestration and lifecycle management."""

import logging
import time
import signal
import atexit
import sys

from pynput import keyboard, mouse

from .activity_tracker import ActivityTracker
from .model.app_config import AppConfig
from .model.app_state import AppState
from .model.state import State, state_to_activity
from .notifier import Notifier
from .session_logger import SessionLogger
from .state_handlers import StateHandler
from .state_persistence import StatePersistence
from .thread_manager import ThreadManager
from .utils import format_duration

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_SECONDS = 5
TEST_MODE_DURATION_MULTIPLIER = 3
TEST_MODE_BUFFER_SECONDS = 1
MINIMUM_SESSION_DURATION_SECONDS = 1


class App:
    """Main application orchestrator managing lifecycle and state machine."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.activity_tracker = ActivityTracker()
        self.session_logger = SessionLogger()
        self.notifier = Notifier()
        self.state_handler = StateHandler(
            self.activity_tracker, self.session_logger, self.notifier
        )
        self.state_persistence = StatePersistence()
        self.thread_manager = ThreadManager()
        self.app_state = self._initialize_app_state()
        self.all_threads = []
        self.last_save_time = time.time()

    def run(self):
        """Main entry point: initialize components and run the state machine."""
        self._resume_from_saved_state()
        self._configure_for_test_mode()
        logger.info("--- Activity Monitor Started (Config: %s) ---", self.config)

        self.all_threads = self._setup_monitoring_system()
        self.thread_manager.start_all(self.all_threads)
        self._register_signal_handlers()

        if self.config.test_mode:
            self._run_main_test_loop()
        else:
            self._run_main_loop()

        self._cleanup_and_shutdown()

    def _initialize_app_state(self) -> AppState:
        """Return initial IDLE state with current timestamps."""
        return AppState(
            current_state=State.IDLE,
            session_start_time=time.time(),
            session_start_monotonic=time.monotonic(),
            activation_candidate_start_monotonic=None,
            break_reminder_shown=False,
        )

    def _resume_from_saved_state(self):
        """Try to load previously saved runtime state and resume from it."""
        resumed_from_saved_state = False
        try:
            saved = self.state_persistence.load(self.config)
            if saved:
                saved_state_name = saved.get("current_state")
                try:
                    saved_state = State[saved_state_name]
                except Exception:
                    saved_state = self.app_state.current_state

                saved_session_start = float(
                    saved.get("session_start_time", self.app_state.session_start_time)
                )
                saved_break_reminder = bool(saved.get("break_reminder_shown", False))
                saved_last_activity = float(
                    saved.get("last_activity_time", time.time())
                )

                current_time = time.time()
                current_monotonic = time.monotonic()
                time_since_last_activity = current_time - saved_last_activity

                if (
                    saved_state == State.ACTIVE
                    and time_since_last_activity >= self.config.break_duration_sec
                ):
                    active_session_end = (
                        saved_last_activity + self.config.break_duration_sec
                    )
                    active_session_duration = active_session_end - saved_session_start

                    if active_session_duration > MINIMUM_SESSION_DURATION_SECONDS:
                        self.session_logger.log(
                            self.config,
                            state_to_activity(saved_state),
                            saved_session_start,
                            active_session_end,
                            active_session_duration,
                        )

                    break_duration = current_time - active_session_end
                    self.notifier.show(
                        "Welcome Back!",
                        f"Your break lasted {format_duration(break_duration)}.",
                        "Starting new session.",
                    )

                    self.app_state = self.app_state._replace(
                        current_state=State.IDLE,
                        session_start_time=active_session_end,
                        session_start_monotonic=current_monotonic,
                        activation_candidate_start_monotonic=None,
                        break_reminder_shown=False,
                    )
                    self.activity_tracker.set_last_activity_time(
                        saved_last_activity, current_monotonic
                    )
                else:
                    self.app_state = self.app_state._replace(
                        current_state=saved_state,
                        session_start_time=saved_session_start,
                        session_start_monotonic=current_monotonic,
                        activation_candidate_start_monotonic=None,
                        break_reminder_shown=saved_break_reminder,
                    )
                    self.activity_tracker.set_last_activity_time(
                        current_time, current_monotonic
                    )

                resumed_from_saved_state = True
                logger.info("Resumed state from saved runtime state: %s", saved)
        except Exception:
            logger.exception("Failed to load saved runtime state")

        if not resumed_from_saved_state:
            self.activity_tracker.set_last_activity_time(
                self.app_state.session_start_time,
                self.app_state.session_start_monotonic,
            )

    def _configure_for_test_mode(self):
        """Modify config for test mode."""
        if not self.config.test_mode:
            return

        logger.info("--- Test mode ---")
        test_csv_file = self.config.csv_file.with_stem(
            f"test_{self.config.csv_file.stem}"
        )
        self.config = self.config._replace(csv_file=test_csv_file)

    def _setup_monitoring_system(self) -> list:
        """Create and return all monitoring threads and listeners."""
        mouse_listener = mouse.Listener(
            on_move=self.activity_tracker.on_activity,
            on_click=self.activity_tracker.on_activity,
            on_scroll=self.activity_tracker.on_activity,
        )
        keyboard_listener = keyboard.Listener(
            on_press=self.activity_tracker.on_activity
        )
        return [mouse_listener, keyboard_listener]

    def _register_signal_handlers(self):
        """Register signal handlers to save state on termination."""

        def _save_state_and_exit(signum=None, frame=None):
            logger.info("Received signal %s - saving runtime state and exiting", signum)
            try:
                self.state_persistence.save(
                    self.config,
                    self.app_state,
                    self.activity_tracker.get_last_activity_time(),
                )
            except Exception:
                logger.exception("Failed to save runtime state in signal handler")
            try:
                sys.exit(0)
            except SystemExit:
                raise

        try:
            signal.signal(signal.SIGINT, _save_state_and_exit)
        except Exception:
            logger.exception("Failed to register SIGINT handler")
        try:
            signal.signal(signal.SIGTERM, _save_state_and_exit)
        except Exception:
            logger.debug("SIGTERM not available on this platform")

        def _on_exit():
            try:
                self.state_persistence.save(
                    self.config,
                    self.app_state,
                    self.activity_tracker.get_last_activity_time(),
                )
            except Exception:
                logger.exception("Failed to save runtime state in atexit handler")

        atexit.register(_on_exit)

    def _run_main_loop(self):
        """Run main state machine loop until interrupted."""
        try:
            while True:
                self._process_current_state()
                self._periodic_state_save()
                time.sleep(COLLECTION_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logger.info("--- KeyboardInterrupt detected. Quitting ---")

    def _run_main_test_loop(self):
        """Run state machine loop for limited test duration."""
        start_time = time.time()
        test_duration = (
            COLLECTION_INTERVAL_SECONDS * TEST_MODE_DURATION_MULTIPLIER
            + TEST_MODE_BUFFER_SECONDS
        )

        while time.time() - start_time < test_duration:
            self._process_current_state()
            time.sleep(COLLECTION_INTERVAL_SECONDS)

        logger.info("--- Test mode: Exiting after %s seconds. ---", test_duration)

    def _process_current_state(self):
        """Process current state and update state."""
        if self.app_state.current_state == State.ACTIVE:
            self.app_state = self.state_handler.handle_active_state(
                self.app_state, self.config
            )
        elif self.app_state.current_state == State.IDLE:
            self.app_state = self.state_handler.handle_idle_state(
                self.app_state, self.config
            )

    def _periodic_state_save(self):
        """Periodically save state to disk to handle unexpected shutdowns."""
        current_time = time.time()
        if current_time - self.last_save_time >= self.config.break_duration_sec:
            try:
                self.state_persistence.save(
                    self.config,
                    self.app_state,
                    self.activity_tracker.get_last_activity_time(),
                )
                self.last_save_time = current_time
            except Exception:
                logger.exception("Failed to save runtime state during periodic save")

    def _cleanup_and_shutdown(self):
        """Cleanup and graceful shutdown of all components."""
        logger.info("Shutting down. Saving final session.")
        self._log_final_session()

        try:
            self.state_persistence.save(
                self.config,
                self.app_state,
                self.activity_tracker.get_last_activity_time(),
            )
        except Exception:
            logger.exception("Failed to save runtime state during cleanup")

        self.thread_manager.cleanup(self.all_threads)
        logger.info("Listeners stopped. Exiting.")

    def _log_final_session(self):
        """Log final session if duration meets minimum threshold."""
        final_time = time.time()
        try:
            session_duration = time.monotonic() - self.app_state.session_start_monotonic
        except Exception:
            session_duration = final_time - self.app_state.session_start_time

        if session_duration > MINIMUM_SESSION_DURATION_SECONDS:
            self.session_logger.log(
                self.config,
                state_to_activity(self.app_state.current_state),
                self.app_state.session_start_time,
                final_time,
                session_duration,
            )
