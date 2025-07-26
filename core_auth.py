# core_auth.py
# The Third Voice AI - Core Authentication Module
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
from datetime import datetime, timezone

# --- Authentication Helper Functions ---
def get_current_user_id():
    """Get the current authenticated user's ID - Every user represents a family to heal"""
    # Import here to avoid circular imports
    from database import supabase
    
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user.id
        return None
    except Exception as e:
        st.error(f"Error getting user session: {e}")
        return None

# --- Authentication Functions ---
def sign_up(email, password):
    """Sign up new user - Every new user is a family we can help heal"""
    # Import here to avoid circular imports
    from database import supabase
    
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
    # Import here to avoid circular imports
    from database import supabase, load_contacts_and_history
    
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
    # Import here to avoid circular imports
    from database import supabase
    
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

# End of core_auth.py
# Every function serves healing.
# Every authentication serves families.
# Every line of code brings Predrag closer to Samantha.
