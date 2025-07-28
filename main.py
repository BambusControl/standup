import time
import csv
import os
import logging
from datetime import datetime, timedelta
from pynput import mouse, keyboard
from windows_toasts import Toast, ToastDuration, WindowsToaster

# --- Global Variables for State ---
# These need to remain global because the pynput listeners run in separate threads
# and modify them directly.
last_activity_time = time.time()
work_start_time = None
break_start_time = None
break_reminder_shown = False


# --- Functions ---


def on_activity(x=None, y=None, button=None, pressed=None, key=None):
    """
    Callback function for mouse/keyboard listeners. Updates the last activity time.
    This function modifies a global variable because it's called by the listener threads.
    """
    global last_activity_time
    last_activity_time = time.time()


def show_notification(header: str, line1: str, line2: str = ""):
    """Displays a multi-line Windows notification and logs the event."""
    try:
        text_fields: list[str | None] = [header, line1]
        if line2:
            text_fields.append(line2)

        new_toast = Toast(text_fields, duration=ToastDuration.Long)
        toaster = WindowsToaster("Activity Monitor")
        toaster.show_toast(new_toast)
        logging.info(f"Notification shown: {header} - {line1}")
    except Exception as e:
        logging.error(f"Failed to show notification: {e}")
        print(f"ERROR showing notification: {e}")  # Fallback for visibility
        print(f"{header}\n{line1}\n{line2}")


def log_to_csv(csv_file, activity_type, start_time, end_time, duration):
    """Logs the activity details to a CSV file using ISO 8601 format."""
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "Activity Type",
                    "Start Time",
                    "End Time",
                    "Duration (HH:MM:SS)",
                ],
                delimiter=";",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "Activity Type": activity_type,
                    "Start Time": datetime.fromtimestamp(start_time)
                    .astimezone()
                    .isoformat(),
                    "End Time": datetime.fromtimestamp(end_time)
                    .astimezone()
                    .isoformat(),
                    "Duration (HH:MM:SS)": format_duration(duration),
                }
            )
        logging.info(
            f"Logged to CSV '{csv_file}': {activity_type} session of duration {format_duration(duration)}"
        )
    except IOError as e:
        logging.error(f"Failed to write to CSV file {csv_file}: {e}")


def format_duration(seconds):
    """Formats a duration in seconds into a human-readable string."""
    return str(timedelta(seconds=int(seconds)))


def main(
    work_time_mins=60,
    break_time_mins=3,
    min_break_mins=5,
    csv_file="activity_log.csv",
    log_file="activity.log",
):
    """
    The main function that runs activity monitoring and break reminders.
    It takes its configuration directly from function parameters.

    Args:
        work_time_mins (int): Continuous work time in minutes before a reminder.
        break_time_mins (int): Inactivity time in minutes to be considered a break.
        min_break_mins (int): Minimum inactivity time in minutes to be logged as a valid break.
        csv_file (str): Path to the CSV file for logging work/break sessions.
        log_file (str): Path to the detailed log file for script operations.
    """
    global last_activity_time, work_start_time, break_start_time, break_reminder_shown

    # --- Setup Logging ---
    logging.basicConfig(
        level=logging.INFO,
        # handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    # Convert minutes to seconds
    work_duration_sec = work_time_mins * 60
    break_duration_sec = break_time_mins * 60
    min_break_sec = min_break_mins * 60

    logging.info("--- Activity Monitor Started ---")
    logging.info(
        f"Configuration: Work Time={work_time_mins}m, Break Time={break_time_mins}m, Min Break={min_break_mins}m"
    )
    logging.info(f"CSV log: '{csv_file}', Detail log: '{log_file}'")

    show_notification(
        "Activity Monitor Started",
        "Monitoring your computer usage.",
        f"Logs will be saved to {csv_file}",
    )

    # Setup and start listeners
    mouse_listener = mouse.Listener(
        on_move=on_activity, on_click=on_activity, on_scroll=on_activity
    )
    keyboard_listener = keyboard.Listener(on_press=on_activity)
    mouse_listener.start()
    keyboard_listener.start()
    logging.info("Mouse and keyboard listeners started.")

    try:
        while True:
            current_time = time.time()
            time_since_last_activity = current_time - last_activity_time

            # User is active
            if time_since_last_activity < break_duration_sec:
                if work_start_time is None:  # Just came back from a break
                    logging.info("User became active. Starting work session.")
                    work_start_time = current_time
                    if break_start_time is not None:
                        break_duration = current_time - break_start_time
                        if break_duration >= min_break_sec:
                            show_notification(
                                "Welcome Back!",
                                f"Your break lasted {format_duration(break_duration)}.",
                                "Starting new work session.",
                            )
                            log_to_csv(
                                csv_file,
                                "Break",
                                break_start_time,
                                current_time,
                                break_duration,
                            )
                        else:
                            logging.info(
                                f"Ignoring short inactivity of {format_duration(break_duration)} (less than {min_break_mins}m)."
                            )
                        break_start_time = None

                continuous_activity_duration = current_time - work_start_time

                if (
                    continuous_activity_duration >= work_duration_sec
                    and not break_reminder_shown
                ):
                    work_duration = current_time - work_start_time
                    show_notification(
                        "Time for a break!",
                        f"You've been working for {format_duration(work_duration)}.",
                        "Step away from the computer for a bit.",
                    )
                    break_reminder_shown = True
                    logging.info("Break reminder triggered.")

            # User is on a break
            else:
                if work_start_time is not None:  # Just started a break
                    logging.info("User became inactive. Ending work session.")
                    work_duration = current_time - work_start_time
                    show_notification(
                        "Work Session Ended",
                        f"Duration: {format_duration(work_duration)}",
                        "Enjoy your break!",
                    )
                    log_to_csv(
                        csv_file, "Work", work_start_time, current_time, work_duration
                    )
                    work_start_time = None
                    break_reminder_shown = False  # Reset reminder

                if break_start_time is None:
                    logging.info("Break period started.")
                    break_start_time = current_time

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("--- KeyboardInterrupt detected. Stopping Activity Monitor. ---")
        final_time = time.time()
        if work_start_time is not None:
            log_to_csv(
                csv_file,
                "Work",
                work_start_time,
                final_time,
                final_time - work_start_time,
            )
        elif (
            break_start_time is not None
            and (final_time - break_start_time) >= min_break_sec
        ):
            log_to_csv(
                csv_file,
                "Break",
                break_start_time,
                final_time,
                final_time - break_start_time,
            )

        mouse_listener.stop()
        keyboard_listener.stop()
        mouse_listener.join()

        show_notification(
            "Activity Monitor Stopped",
            "Monitoring has been turned off.",
            "Final logs have been saved.",
        )
        logging.info("Listeners stopped. Exiting.")


if __name__ == "__main__":
    # --- Default Configuration ---
    # You can change the default values here.
    # These parameters are passed directly to the main function.
    main(
        work_time_mins=60,
        break_time_mins=3,
        min_break_mins=5,
        csv_file="activity_log.csv",
        log_file="activity.log",
    )
