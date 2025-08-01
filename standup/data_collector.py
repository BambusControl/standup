import csv
import logging
import time
import threading

import pygetwindow as gw

from pathlib import Path
from pynput import mouse, keyboard

# --- Configuration ---
# Using a list for the CSV header for consistency.
CSV_HEADER = [
    "timestamp",
    "mouse_moves_count",
    "mouse_clicks_count",
    "mouse_scrolls_count",
    "key_presses_count",
    "last_window_title",
    "activity_detected",
]

COLLECTION_INTERVAL_SECONDS = 5

# --- Private State ---
_polling_stop_event = threading.Event()
_summary_logging_stop_event = threading.Event()
_event_buffer = []
_buffer_lock = threading.Lock()

_last_known_window_title = None
# _last_known_process_name removed


def _log_event(event_data: dict):
    """Adds a single event dictionary to the thread-safe buffer."""
    with _buffer_lock:
        _event_buffer.append(event_data)


def _write_summary_row(summary_data: dict, log_file_path):
    """Writes a single summary row to the CSV file."""
    if not log_file_path:
        return

    # Always append to the log file
    write_mode = "a"

    try:
        with log_file_path.open(write_mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER, delimiter=";")
            # Write header only if file is new or empty
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(summary_data)
    except IOError as e:
        logging.error(f"[DataCollector] Failed to write to raw log file: {e}")


def _log_summary_data():
    """Processes the event buffer and logs a summary row every second."""
    global _last_known_window_title, _current_log_file_path
    last_processed_timestamp = time.time()

    while not _summary_logging_stop_event.is_set():
        current_second_start = time.time()
        events_in_second = []

        with _buffer_lock:
            # Extract events that occurred in the last second
            i = 0
            while i < len(_event_buffer):
                if _event_buffer[i]["timestamp"] >= last_processed_timestamp:
                    events_in_second.append(_event_buffer.pop(i))
                else:
                    i += 1
            last_processed_timestamp = current_second_start

        # Aggregate data for the current second
        mouse_moves = 0
        mouse_clicks = 0
        mouse_scrolls = 0
        key_presses = 0
        # Initialize with last known values
        current_window_title = _last_known_window_title
        activity_detected = False

        for event in events_in_second:
            if event["event_type"] == "mouse_move":
                mouse_moves += 1
                activity_detected = True
            elif event["event_type"] == "mouse_click":
                mouse_clicks += 1
                activity_detected = True
            elif event["event_type"] == "mouse_scroll":
                mouse_scrolls += 1
                activity_detected = True
            elif event["event_type"] == "key_press":
                key_presses += 1
                activity_detected = True
            elif event["event_type"] == "active_window_poll":
                current_window_title = event.get("window_title")
                # Update global last known values
                _last_known_window_title = current_window_title

        summary_row = {
            "timestamp": current_second_start,
            "mouse_moves_count": mouse_moves,
            "mouse_clicks_count": mouse_clicks,
            "mouse_scrolls_count": mouse_scrolls,
            "key_presses_count": key_presses,
            "last_window_title": current_window_title,
            "activity_detected": int(activity_detected),
        }
        _write_summary_row(summary_row, _current_log_file_path)

        # Wait for the next second, adjusting for processing time
        time_to_wait = COLLECTION_INTERVAL_SECONDS - (
            time.time() - current_second_start
        )
        if time_to_wait > 0:
            _summary_logging_stop_event.wait(time_to_wait)


# --- Pynput Callback Functions ---


def _on_move(x, y):
    _log_event({"timestamp": time.time(), "event_type": "mouse_move"})


def _on_click(x, y, button, pressed):
    _log_event({"timestamp": time.time(), "event_type": "mouse_click"})


def _on_scroll(x, y, dx, dy):
    _log_event({"timestamp": time.time(), "event_type": "mouse_scroll"})


def _on_press(key):
    _log_event({"timestamp": time.time(), "event_type": "key_press"})


# --- Public API ---


def start_data_collection(log_file: Path):
    """
    Initializes and starts the raw data collection listeners and window poller in the background.
    """
    global _current_log_file_path
    _current_log_file_path = Path(log_file)

    mouse_listener = mouse.Listener(
        on_move=_on_move, on_click=_on_click, on_scroll=_on_scroll
    )
    keyboard_listener = keyboard.Listener(on_press=_on_press)

    # Create the active window polling thread, but don't start it yet
    polling_thread = threading.Thread(target=_poll_active_window, daemon=True)

    # Create the summary logging thread
    summary_logging_thread = threading.Thread(target=_log_summary_data, daemon=True)

    logging.info(
        f"[DataCollector] Raw data collection listeners and window poller created. Logging to '{log_file}'"
    )
    return [mouse_listener, keyboard_listener, polling_thread, summary_logging_thread]


def stop_data_collection():
    """Signals the active window polling thread and summary logging thread to stop."""
    _polling_stop_event.set()
    _summary_logging_stop_event.set()


def _poll_active_window():
    """Periodically polls the active window and logs its details."""
    while not _polling_stop_event.is_set():
        try:
            active_window = gw.getActiveWindow()

            if active_window:
                _log_event(
                    {
                        "timestamp": time.time(),
                        "event_type": "active_window_poll",
                        "window_title": active_window.title,
                    }
                )
            else:
                _log_event(
                    {
                        "timestamp": time.time(),
                        "event_type": "active_window_poll",
                        "window_title": "No active window",
                    }
                )
        except Exception as e:
            logging.error(f"[DataCollector] Error polling active window: {e}")

        _polling_stop_event.wait(
            COLLECTION_INTERVAL_SECONDS
        )  # Poll every COLLECTION_INTERVAL_SECONDS seconds
