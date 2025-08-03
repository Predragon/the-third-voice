import streamlit as st
from supabase import create_client, Client
import requests
from datetime import datetime, timezone
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Constants ---
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-2-9b-it:free"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    try:
        return create_client(st.secrets.supabase.url, st.secrets.supabase.key)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

supabase = init_supabase()

# --- Session State ---
def init_session_state():
    defaults = {
        'authenticated': False,
        'user': None,
        'app_mode': "login",
        'contacts': {},
        'active_contact': None,
        'conversation_input_text': "",
        'last_output': None,
        'last_mode': None,
        'failed_writes': {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Auth Functions ---
def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            st.session_state.show_verification_notice = True
            st.session_state.verification_email = email
            st.session_state.app_mode = "verification_notice"
            st.rerun()
    except Exception as e:
        st.error(f"Sign up failed: {e}")

def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def sign_out():
    supabase.auth.sign_out()
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.app_mode = "login"
    st.rerun()

# --- Database Operations ---
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def save_message(data):
    try:
        response = supabase.table("messages").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Database error: {e}")
        raise

def load_contacts():
    user_id = get_current_user_id()
    if not user_id: return {}
    response = supabase.table("contacts").select("*").eq("user_id", user_id).execute()
    return {c["name"]: c for c in response.data}

# --- AI Processing ---
def process_ai_action(mode, message, contact_name, context):
    prompts = {
        "transform": f"Improve this {context} message: '{message}'",
        "interpret": f"Analyze this {context} message: '{message}'"
    }
    
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {st.secrets.openrouter.api_key}"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompts[mode]}],
                "max_tokens": 500
            },
            timeout=15
        ).json()
        
        result = response["choices"][0]["message"]["content"]
        
        save_message({
            "contact_id": st.session_state.contacts[contact_name]["id"],
            "message_type": mode,
            "original": message,
            "result": result,
            "user_id": get_current_user_id()
        })
        
        return result
    except Exception as e:
        st.error(f"AI processing failed: {e}")
        return None

# --- UI Pages ---
def render_auth_pages():
    if st.session_state.app_mode == "login":
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                sign_in(email, password)
            if st.button("Create Account"):
                st.session_state.app_mode = "signup"
                st.rerun()
    
    elif st.session_state.app_mode == "signup":
        with st.form("signup"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                sign_up(email, password)

def render_contacts_list():
    st.session_state.contacts = load_contacts()
    for name, data in st.session_state.contacts.items():
        if st.button(name):
            st.session_state.active_contact = name
            st.session_state.app_mode = "conversation_view"
            st.rerun()
    if st.button("Add Contact"):
        st.session_state.app_mode = "add_contact"

def render_conversation_view():
    contact_name = st.session_state.active_contact
    message = st.text_area("Message", key="conversation_input_text")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Transform"):
            st.session_state.last_output = process_ai_action("transform", message, contact_name, "general")
            st.session_state.last_mode = "transform"
    with col2:
        if st.button("Interpret"):
            st.session_state.last_output = process_ai_action("interpret", message, contact_name, "general")
            st.session_state.last_mode = "interpret"
    
    if st.session_state.last_output:
        st.write(st.session_state.last_output)

# --- Main App ---
def main():
    st.set_page_config(page_title="The Third Voice", page_icon="🎙️")
    
    if not st.session_state.authenticated:
        render_auth_pages()
    else:
        if st.session_state.app_mode == "contacts_list":
            render_contacts_list()
        elif st.session_state.app_mode == "conversation_view":
            render_conversation_view()
    
    if st.session_state.authenticated and st.button("Logout"):
        sign_out()

if __name__ == "__main__":
    main()
