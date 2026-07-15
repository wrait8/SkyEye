# Modules/ui_utils.py
"""
UI Utility Functions
Handles terminal UI elements like spinners and animations
"""

import sys
import time
from itertools import cycle


def spinning_cursor():
    """Generator for spinner animation frames"""
    frames = ["[-]", r"[\]", "[|]", "[/]"]
    return cycle(frames)


def spinner(duration_sec: float = 3, message: str = "Loading"):
    """
    Display a spinner animation in the terminal
    
    Args:
        duration_sec: How long to display the spinner
        message: Message to display with the spinner
    """
    spinner_gen = spinning_cursor()
    end_time = time.time() + duration_sec
    
    while time.time() < end_time:
        sys.stdout.write(f"\r{next(spinner_gen)} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
    
    # Clear the spinner
    sys.stdout.write("\r" + " " * (len(message) + 5) + "\r")
    sys.stdout.flush()
