# core_auth_module.py - The Complete Foundation
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime, timezone
import time
import requests

# --- Constants ---
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Co-parenting relationships"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Family connections"},
    "friend": {"icon": "🤝", "description": "Friendships"}
}

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.stop()

supabase = init_supabase_connection()

# --- Authentication Pages ---
def verification_notice_page():
    st.title("🎙️ Email Verification")
    st.info("""
    A verification link has been sent to your email.
    Please check your inbox and verify your account.
    """)
    if st.button("Return to Login"):
        st.session_state.app_mode = "login"
        st.rerun()

def login_page():
    st.title("🎙️ The Third Voice AI")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state.authenticated = True
                    st.session_state.user = res.user
                    st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

def signup_page():
    st.title("🎙️ Create Account")
    with st.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign Up"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                if res.user:
                    st.session_state.app_mode = "verification_notice"
                    st.rerun()
            except Exception as e:
                st.error(f"Signup failed: {str(e)}")

# --- UI Components ---
def render_first_time_screen():
    st.title("👋 Welcome to The Third Voice")
    # ... [your existing first-time setup UI] ...

def render_contacts_list_view():
    st.title("📞 Your Contacts")
    # ... [your existing contacts list UI] ...

def render_add_contact_view():
    st.title("➕ Add New Contact")
    # ... [your existing add contact UI] ...

def render_edit_contact_view():
    st.title("✏️ Edit Contact")
    # ... [your existing edit contact UI] ...

# --- Core Functions ---
def init_session_state():
    defaults = {
        'authenticated': False,
        'user': None,
        'app_mode': "login",
        'contacts': {},
        'active_contact': None,
        'edit_contact': None,
        'last_error_message': None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def get_current_user_id():
    try:
        session = supabase.auth.get_session()
        return session.user.id if session and session.user else None
    except Exception as e:
        st.error(f"User check failed: {str(e)}")
        return None

def create_message_hash(message, context):
    return hashlib.md5(f"{message}{context}".encode()).hexdigest()

def sign_out():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()

# ... [include all other missing functions your app.py expects] ...
