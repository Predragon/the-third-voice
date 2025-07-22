# the-third-voice/app.py
import streamlit as st
import json
import datetime
import requests
from supabase import create_client

# Constants
CONTEXTS = ["romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load Supabase History

def load_supabase_history():
    try:
        response = supabase.table("messages").select("*").order("timestamp").execute()
        messages = response.data
        contacts = {context: {'context': context, 'history': []} for context in CONTEXTS}

        for msg in messages:
            contact_name = msg["contact_name"]
            if contact_name not in contacts:
                contacts[contact_name] = {'context': "family", 'history': []}  # fallback context
            contacts[contact_name]['history'].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "sentiment": msg["sentiment"],
                "model": msg["model"]
            })

        return contacts
    except Exception as e:
        st.warning(f"⚠️ Could not load history from Supabase: {e}")
        return {context: {'context': context, 'history': []} for context in CONTEXTS}

# Initialize Session State
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets["openrouter"]["api_key"],
        'contacts': load_supabase_history(),
        'active_contact': CONTEXTS[0],
        'journal_entries': {},
        'feedback_data': {},
        'user_stats': {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0},
        'active_mode': None
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

initialize_session()

# Token Validation
def validate_token():
    if REQUIRE_TOKEN and not st.session_state.token_validated:
        st.markdown("# 🎙️ The Third Voice\n*Your AI Communication Coach*")
        st.warning("🔐 Access restricted. Enter beta token to continue.")
        token = st.text_input("Token:", type="password")
        if st.button("Validate"):
            if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
                st.session_state.token_validated = True
                st.success("✅ Authorized")
                st.rerun()
            else:
                st.error("Invalid token")
        st.stop()

validate_token()

# Contact/Context Selection UI
def contact_sidebar():
    st.sidebar.markdown("### 👥 Contacts & Contexts")
    with st.sidebar.expander("➕ Add Contact"):
        new_name = st.text_input("Contact Name")
        new_context = st.selectbox("Relationship Context", CONTEXTS)
        if st.button("Add Contact") and new_name:
            if new_name not in st.session_state.contacts:
                st.session_state.contacts[new_name] = {"context": new_context, "history": []}
                st.session_state.active_contact = new_name
                st.success(f"Added contact: {new_name}")
                st.rerun()
            else:
                st.warning("Contact already exists")

    contact_names = list(st.session_state.contacts.keys())
    selected = st.sidebar.selectbox("Select Contact", contact_names, index=contact_names.index(st.session_state.active_contact))
    st.session_state.active_contact = selected

contact_sidebar()
