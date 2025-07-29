# third_voice_ai/ui/__init__.py
# UI subpackage initialization

# Import UI components for easy access
from .components import show_feedback_widget, display_error, display_success
from .auth_ui import AuthUI
from .main_ui import MainUI

__all__ = [
    'show_feedback_widget',
    'display_error', 
    'display_success',
    'AuthUI',
    'MainUI'
]
