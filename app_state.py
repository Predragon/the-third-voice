# app_state.py
# The Third Voice AI - Application State & Constants Module
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st

# --- Relationship Context Constants ---
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables - Foundation for healing journeys"""
    defaults = {
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
        # Model fallback state
        'current_model_index': 0,
        'last_successful_model': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# End of app_state.py
# Every constant serves healing.
# Every state variable fights for families.
# Every line of code brings Predrag closer to Samantha.
