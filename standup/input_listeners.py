"""
Input event listeners for activity monitoring.

This module provides input event listeners for mouse and keyboard activity
that feed into the event buffer system.
"""

from pynput import mouse, keyboard

from .event_buffer import (
    log_mouse_move,
    log_mouse_click,
    log_mouse_scroll,
    log_key_press,
)


def create_input_listeners() -> list:
    """
    Create input listeners for mouse and keyboard events.

    Returns:
        List of listener objects for mouse and keyboard
    """
    mouse_listener = mouse.Listener(
        on_move=_on_move, on_click=_on_click, on_scroll=_on_scroll
    )
    keyboard_listener = keyboard.Listener(on_press=_on_press)

    return [mouse_listener, keyboard_listener]


# Pynput callback functions for capturing user input events


def _on_move(x, y):
    """Callback for mouse movement events."""
    log_mouse_move()


def _on_click(x, y, button, pressed):
    """Callback for mouse click events."""
    log_mouse_click()


def _on_scroll(x, y, dx, dy):
    """Callback for mouse scroll events."""
    log_mouse_scroll()


def _on_press(key):
    """Callback for keyboard press events."""
    log_key_press()
