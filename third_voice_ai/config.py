# config.py - The Third Voice AI Configuration
# Central configuration for application settings and constants

# Module-level constants for direct import
APP_NAME = "The Third Voice AI"
APP_ICON = "🎙️"
VERSION = "2.0.0"
MISSION_STATEMENT = "When both people are speaking from pain, someone must be the third voice."

# Supabase Configuration (placeholders, override in Streamlit secrets)
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"

# Relationship Contexts
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships", "default_name": "Partner"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together", "default_name": "Co-parent"},
    "workplace": {"icon": "🏢", "description": "Professional relationships", "default_name": "Colleague"},
    "family": {"icon": "🏠", "description": "Extended family connections", "default_name": "Family Member"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds", "default_name": "Friend"}
}

# Default Session State
DEFAULT_SESSION_STATE = {
    'authenticated': False,
    'user': None,
    'app_mode': "login",
    'contacts': {},
    'active_contact': None,
    'edit_contact': None,
    'conversation_input_text': "",
    'clear_conversation_input': False,
    'edit_contact_name_input': "",
    'add_contact_name_input': "",
    'add_contact_context_select': list(CONTEXTS.keys())[0],
    'last_error_message': None,
    'show_verification_notice': False,
    'verification_email': None,
    'logged_out_intentionally': False
}

# Error Messages
ERROR_MESSAGES = {
    "no_api_key": "OpenRouter API Key not found in Streamlit secrets under [openrouter]. Please add it.",
    "no_supabase_config": "Missing Streamlit secret. Please ensure [supabase] url and key are set in your secrets.",
    "empty_message": "Input message cannot be empty. Please type something to transform.",
    "contact_not_found": "Contact not found.",
    "network_timeout": "API request timed out. Please try again.",
    "connection_error": "Connection error. Please check your internet connection.",
    "authentication_failed": "Authentication failed. Please check your credentials.",
    "database_error": "Database error occurred. Please try again."
}

# UI Messages
UI_MESSAGES = {
    "welcome_first_time": "Choose a relationship type to get started, or add a custom contact:",
    "no_contacts": "No contacts yet. Add your first contact to get started!",
    "guidance_placeholder": "Your Third Voice guidance will appear here after you click Transform",
    "healing_mission": "We help families heal through better conversations.",
    "verification_sent": "Verification email sent. Please check your inbox and spam folder."
}

# Feature Flags
ENABLE_ANALYTICS = True
ENABLE_FEEDBACK = True
ENABLE_INTERPRETATION = True
ENABLE_RELATIONSHIP_PROGRESS = True
ENABLE_OFFLINE_MODE = True

# AI Model Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-2-9b-it:free"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500
API_TIMEOUT = 25

# Streamlit Configuration
PAGE_CONFIG = {
    "page_title": APP_NAME,
    "page_icon": APP_ICON,
    "layout": "centered",
    "initial_sidebar_state": "collapsed"
}

# Database Configuration
CACHE_TTL = 30  # seconds
MESSAGE_HISTORY_LIMIT = 10
RECENT_MESSAGES_DISPLAY = 3

# Mobile Optimization
MOBILE_BREAKPOINT = 768
COMPACT_MODE_THRESHOLD = 600

# Scoring System
HEALING_SCORE_THRESHOLDS = {
    "excellent": 8,
    "good": 6,
    "basic": 4
}

# Rate Limiting
MAX_REQUESTS_PER_HOUR = 100
CACHE_EXPIRY_HOURS = 24

class Config:
    """Configuration class for The Third Voice AI"""
    
    APP_NAME = APP_NAME
    APP_ICON = APP_ICON
    VERSION = VERSION
    MISSION_STATEMENT = MISSION_STATEMENT
    SUPABASE_URL = SUPABASE_URL
    SUPABASE_KEY = SUPABASE_KEY
    CONTEXTS = CONTEXTS
    DEFAULT_SESSION_STATE = DEFAULT_SESSION_STATE
    ERROR_MESSAGES = ERROR_MESSAGES
    UI_MESSAGES = UI_MESSAGES
    ENABLE_ANALYTICS = ENABLE_ANALYTICS
    ENABLE_FEEDBACK = ENABLE_FEEDBACK
    ENABLE_INTERPRETATION = ENABLE_INTERPRETATION
    ENABLE_RELATIONSHIP_PROGRESS = ENABLE_RELATIONSHIP_PROGRESS
    ENABLE_OFFLINE_MODE = ENABLE_OFFLINE_MODE
    API_URL = API_URL
    MODEL = MODEL
    DEFAULT_TEMPERATURE = DEFAULT_TEMPERATURE
    DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS
    API_TIMEOUT = API_TIMEOUT
    PAGE_CONFIG = PAGE_CONFIG
    CACHE_TTL = CACHE_TTL
    MESSAGE_HISTORY_LIMIT = MESSAGE_HISTORY_LIMIT
    RECENT_MESSAGES_DISPLAY = RECENT_MESSAGES_DISPLAY
    MOBILE_BREAKPOINT = MOBILE_BREAKPOINT
    COMPACT_MODE_THRESHOLD = COMPACT_MODE_THRESHOLD
    HEALING_SCORE_THRESHOLDS = HEALING_SCORE_THRESHOLDS
    MAX_REQUESTS_PER_HOUR = MAX_REQUESTS_PER_HOUR
    CACHE_EXPIRY_HOURS = CACHE_EXPIRY_HOURS

# Global config instance
config = Config()

__all__ = [
    'APP_NAME', 'APP_ICON', 'VERSION', 'MISSION_STATEMENT',
    'SUPABASE_URL', 'SUPABASE_KEY', 'CONTEXTS', 'DEFAULT_SESSION_STATE',
    'ERROR_MESSAGES', 'UI_MESSAGES', 'ENABLE_ANALYTICS', 'ENABLE_FEEDBACK',
    'ENABLE_INTERPRETATION', 'ENABLE_RELATIONSHIP_PROGRESS', 'ENABLE_OFFLINE_MODE',
    'API_URL', 'MODEL', 'DEFAULT_TEMPERATURE', 'DEFAULT_MAX_TOKENS', 'API_TIMEOUT',
    'PAGE_CONFIG', 'CACHE_TTL', 'MESSAGE_HISTORY_LIMIT', 'RECENT_MESSAGES_DISPLAY',
    'MOBILE_BREAKPOINT', 'COMPACT_MODE_THRESHOLD', 'HEALING_SCORE_THRESHOLDS',
    'MAX_REQUESTS_PER_HOUR', 'CACHE_EXPIRY_HOURS', 'Config', 'config'
]
