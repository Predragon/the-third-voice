# core_auth_module.py - The Beating Heart of The Third Voice
import streamlit as st
from supabase import create_client, Client
import os
import hashlib
from datetime import datetime, timezone
import time
import requests

# --- Constants ---
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"🔥 Sacred Connection Failed: {str(e)}")
        st.stop()

supabase = init_supabase_connection()

# --- Session State ---
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

# --- Authentication ---
def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.session_state.contacts = load_contacts_and_history()
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

def sign_out():
    supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Database Operations ---
def load_contacts_and_history():
    user_id = get_current_user_id()
    if not user_id: return {}
    
    try:
        # Load contacts
        contacts_data = {}
        contacts = supabase.table("contacts").select("*").eq("user_id", user_id).execute()
        for contact in contacts.data:
            contacts_data[contact["name"]] = {
                "id": contact["id"],
                "context": contact["context"],
                "history": []
            }
        
        # Load messages
        messages = supabase.table("messages").select("*").eq("user_id", user_id).execute()
        for msg in messages.data:
            contact_name = msg["contact_name"]
            if contact_name in contacts_data:
                contacts_data[contact_name]["history"].append({
                    "id": msg["id"],
                    "time": datetime.fromisoformat(msg["created_at"]).strftime("%m/%d %H:%M"),
                    "type": msg["type"],
                    "original": msg["original"],
                    "result": msg["result"],
                    "healing_score": msg.get("healing_score", 0)
                })
        return contacts_data
    except Exception as e:
        st.warning(f"Database loading failed: {str(e)}")
        return {}

# --- UI Components ---
def login_page():
    st.title("🎙️ The Third Voice AI")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            sign_in(email, password)

# ... [additional auth/crud functions as in your original] ...

# --- Critical Helper Functions ---
def get_current_user_id():
    try:
        session = supabase.auth.get_session()
        return session.user.id if session and session.user else None
    except Exception as e:
        st.error(f"User check failed: {str(e)}")
        return None

def create_message_hash(message, context):
    return hashlib.md5(f"{message}{context}".encode()).hexdigest()
