# modules/utils.py

import time

def typing_delay(text: str, speed: float = 0.02) -> str:
    """
    Simulate typing delay (for future use).
    """
    for char in text:
        print(char, end='', flush=True)
        time.sleep(speed)
    return text

def format_message(author: str, message: str) -> str:
    """
    Simple utility to format chat messages.
    """
    return f"**{author}:** {message}"
