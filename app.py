import streamlit as st
from supabase import create_client, Client
import os
import json
import hashlib
from datetime import datetime, timezone
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Constants ---
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}

# AI Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-2-9b-it:free"

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        supabase_client: Client = create_client(url, key)
        return supabase_client
    except Exception as e:
        st.error(f"Database connection failed: {e}")
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
        'conversation_input_text': "",
        'last_output': None,
        'last_mode': None,
        'failed_writes': {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Helper Functions ---
def get_current_user_id():
    try:
        session = supabase.auth.get_session()
        return session.user.id if session and session.user else None
    except Exception as e:
        st.error(f"Session error: {e}")
        return None

# --- Database Operations (With Recovery) ---
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def save_message_with_retry(data):
    response = supabase.table("messages").insert(data).execute()
    if not response.data:
        raise ValueError("Empty DB response")
    return True

def cache_failed_write(data):
    st.session_state.failed_writes[data["contact_name"]] = data
    st.error("Message saved locally (database offline). Will retry later.")

def retry_failed_writes():
    for contact_name, data in list(st.session_state.failed_writes.items()):
        try:
            if save_message_with_retry(data):
                del st.session_state.failed_writes[contact_name]
        except:
            pass

# --- AI Processing ---
def process_ai_action(mode, message, contact_name, context):
    """Unified handler for both Transform and Interpret"""
    try:
        # System prompts
        prompts = {
            "transform": f"""You are a communication coach. Improve this message for a {context} relationship:
                          "{message}"
                          Provide:
                          1. A kinder version
                          2. Two alternatives
                          3. Brief explanation""",
            "interpret": f"""You are a therapist. Analyze this {context} message:
                           "{message}"
                           Reveal:
                           1. Emotional subtext
                           2. Unmet needs
                           3. Healing opportunities"""
        }
        
        # API call
        headers = {
            "Authorization": f"Bearer {st.secrets.openrouter.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompts[mode]}],
                "max_tokens": 500
            },
            timeout=15
        ).json()
        
        ai_output = response["choices"][0]["message"]["content"]
        
        # Database save
        data = {
            "contact_id": st.session_state.contacts[contact_name]["id"],
            "contact_name": contact_name,
            "message_type": mode,
            "original": message,
            "result": ai_output,
            "healing_score": min(10, len(ai_output) // 50 + 5),
            "user_id": get_current_user_id()
        }
        
        try:
            save_message_with_retry(data)
        except Exception as e:
            cache_failed_write(data)
        
        return ai_output
        
    except Exception as e:
        st.error(f"{mode.capitalize()} failed: {str(e)}")
        return None

# --- UI Pages (Simplified Excerpt) ---
def render_conversation_view():
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {})
    
    # Input area
    message = st.text_area(
        "What's happening?",
        key="conversation_input_text",
        height=120
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Transform My Message", disabled=not message.strip()):
            st.session_state.last_output = process_ai_action(
                "transform", message, contact_name, contact_data["context"]
            )
            st.session_state.last_mode = "transform"
    with col2:
        if st.button("🔍 Interpret Their Message", disabled=not message.strip()):
            st.session_state.last_output = process_ai_action(
                "interpret", message, contact_name, contact_data["context"]
            )
            st.session_state.last_mode = "interpret"
    
    # Display results
    if st.session_state.last_output:
        st.markdown(f"**{'Transformed' if st.session_state.last_mode == 'transform' else 'Interpreted'} Message**")
        st.write(st.session_state.last_output)
    
    # Recovery status
    if st.session_state.failed_writes:
        st.warning(f"{len(st.session_state.failed_writes)} unsaved messages")
        if st.button("Retry Saving"):
            retry_failed_writes()
            st.rerun()

# --- Main App (Retains All Original Routing) ---
def main():
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Retry failed writes on load
    retry_failed_writes()
    
    # Original authentication and page routing logic
    if not st.session_state.authenticated:
        render_auth_pages()  # Your existing login/signup implementation
    else:
        if st.session_state.app_mode == "conversation_view":
            render_conversation_view()
        elif st.session_state.app_mode == "contacts_list":
            render_contacts_list()  # Your existing contacts UI
        # ... (all other original modes)

if __name__ == "__main__":
    main()
