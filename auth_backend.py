# auth_backend.py
# The Third Voice AI - Authentication & App State (After Database Extraction)
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
from database import supabase, get_current_user_id, load_contacts_and_history
from datetime import datetime, timezone

# --- Constants ---
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

# --- Authentication Functions ---
def sign_up(email, password):
    """Sign up new user - Every new user is a family we can help heal"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            # Set verification notice
            st.session_state.show_verification_notice = True
            st.session_state.verification_email = email
            st.session_state.app_mode = "verification_notice"
            st.rerun()
        elif response.error:
            st.error(f"Sign-up failed: {response.error.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred during sign-up: {e}")

def sign_in(email, password):
    """Sign in user - Welcome back to the healing journey"""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.session_state.contacts = load_contacts_and_history()
            if not st.session_state.contacts:
                st.session_state.app_mode = "first_time_setup"
            else:
                st.session_state.app_mode = "contacts_list"
            st.success(f"Welcome back, {response.user.email}!")
            st.rerun()
        elif response.error:
            st.error(f"Login failed: {response.error.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred during login: {e}")

def sign_out():
    """Sign out user - Until we meet again on the healing path"""
    try:
        response = supabase.auth.sign_out()
        if not response.error:
            # Clear all session state
            for key in list(st.session_state.keys()):
                if key not in ['authenticated', 'user', 'app_mode']:
                    del st.session_state[key]
            
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.app_mode = "login"
            
            st.info("You have been logged out.")
            st.rerun()
        else:
            st.error(f"Logout failed: {response.error.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred during logout: {e}")

# End of auth_backend.py
# Every function serves healing.
# Every authentication serves families.
# Every line of code brings Predrag closer to Samantha.
