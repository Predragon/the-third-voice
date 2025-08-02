# config.py - The Third Voice AI Configuration
# Configuration constants and settings for the application

class Config:
    """Configuration class for The Third Voice AI"""
    
    # Application Metadata
    APP_NAME = "The Third Voice AI"
    APP_ICON = "🎙️"
    VERSION = "2.0.0"
    MISSION_STATEMENT = "When both people are speaking from pain, someone must be the third voice."

    # Relationship Contexts
    CONTEXTS = {
        "romantic": {"icon": "💕", "description": "Partner & intimate relationships", "default_name": "Partner"},
        "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together", "default_name": "Co-parent"},
        "workplace": {"icon": "🏢", "description": "Professional relationships", "default_name": "Colleague"},
        "family": {"icon": "🏠", "description": "Extended family connections", "default_name": "Family Member"},
        "friend": {"icon": "🤝", "description": "Friendships & social bonds", "default_name": "Friend"}
    }

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

    # Session State Defaults
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

    # Database Configuration
    CACHE_TTL = 30  # seconds
    MESSAGE_HISTORY_LIMIT = 10
    RECENT_MESSAGES_DISPLAY = 3

    # Feature Flags
    ENABLE_ANALYTICS = True
    ENABLE_FEEDBACK = True
    ENABLE_INTERPRETATION = True
    ENABLE_RELATIONSHIP_PROGRESS = True
    ENABLE_OFFLINE_MODE = True

    # Mobile Optimization
    MOBILE_BREAKPOINT = 768
    COMPACT_MODE_THRESHOLD = 600

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

    # Scoring System
    HEALING_SCORE_THRESHOLDS = {
        "excellent": 8,
        "good": 6,
        "basic": 4
    }

    # Rate Limiting
    MAX_REQUESTS_PER_HOUR = 100
    CACHE_EXPIRY_HOURS = 24

    # Export commonly used items
    __all__ = [
        'APP_NAME', 'APP_ICON', 'VERSION', 'MISSION_STATEMENT',
        'CONTEXTS', 'API_URL', 'MODEL', 'PAGE_CONFIG',
        'DEFAULT_SESSION_STATE', 'ERROR_MESSAGES', 'UI_MESSAGES',
        'ENABLE_ANALYTICS', 'ENABLE_FEEDBACK', 'ENABLE_INTERPRETATION'
    ]

# Global config instance (optional, depending on initialization needs)
config = Config()