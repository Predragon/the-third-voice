import streamlit as st
import datetime
import requests
from supabase import create_client, Client
import os
import json
from datetime import datetime, timezone

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

# --- Supabase Initialization ---
@st.cache_resource
def init_supabase_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        supabase_client: Client = create_client(url, key)
        st.success("Connected to Supabase successfully!")
        return supabase_client
    except KeyError as e:
        st.error(f"Missing Streamlit secret: {e}. Please ensure [supabase] url and key are set in your secrets.")
        st.stop()
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        st.stop()

supabase = init_supabase_connection()

# Session State Initialization
for key, default in {
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
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Helper Functions
def get_current_user_id():
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user.id
        return None
    except Exception as e:
        st.error(f"Error getting user session: {e}")
        return None

def contact_exists_for_user(name, user_id):
    try:
        response = supabase.table("contacts").select("id").eq("name", name).eq("user_id", user_id).execute()
        return bool(response.data) and len(response.data) > 0
    except Exception as e:
        st.warning(f"Error checking contact existence in DB: {e}")
        return False

# Authentication Functions
def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            st.success("Sign-up successful! Please check your email to confirm your account.")
            st.session_state.app_mode = "login"
            st.experimental_rerun()
        elif response.error:
            st.error(f"Sign-up failed: {response.error.message}")
    except Exception as e:
        st.error(f"Error during sign-up: {e}")

def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.session_state.contacts = load_contacts_and_history()
            st.session_state.app_mode = "contacts_list" if st.session_state.contacts else "first_time_setup"
            st.success(f"Welcome back, {response.user.email}!")
            st.experimental_rerun()
        elif response.error:
            st.error(f"Login failed: {response.error.message}")
    except Exception as e:
        st.error(f"Error during login: {e}")

def sign_out():
    try:
        response = supabase.auth.sign_out()
        if not response.error:
            for key in ['authenticated', 'user', 'contacts', 'active_contact', 'edit_contact',
                        'conversation_input_text', 'clear_conversation_input', 'edit_contact_name_input',
                        'add_contact_name_input', 'add_contact_context_select', 'last_error_message', 'app_mode']:
                if key in st.session_state:
                    if key == 'app_mode':
                        st.session_state[key] = "login"
                    elif key == 'authenticated' or key == 'clear_conversation_input':
                        st.session_state[key] = False
                    elif key == 'contacts' or key == 'active_contact' or key == 'edit_contact':
                        st.session_state[key] = {} if key == 'contacts' else None
                    else:
                        st.session_state[key] = ""
            st.info("You have been logged out.")
            st.experimental_rerun()
        else:
            st.error(f"Logout failed: {response.error.message}")
    except Exception as e:
        st.error(f"Error during logout: {e}")

# Data Loading (no cache to avoid stale data during debugging)
def load_contacts_and_history():
    user_id = get_current_user_id()
    if not supabase or not user_id:
        return {}
    try:
        contacts_response = supabase.table("contacts").select("*").eq("user_id", user_id).execute()
        st.write("DEBUG contacts_response.data:", contacts_response.data)
        contacts_data = {c["name"]: {
            "context": c["context"],
            "history": [],
            "created_at": c.get("created_at", datetime.now(timezone.utc).isoformat()),
            "id": c.get("id")
        } for c in contacts_response.data}

        messages_response = supabase.table("messages").select("*").eq("user_id", user_id).order("timestamp").execute()
        st.write("DEBUG messages_response.data:", messages_response.data)

        for msg in messages_response.data:
            contact_name = msg["contact_name"]
            if contact_name not in contacts_data:
                contacts_data[contact_name] = {
                    "context": "family",
                    "history": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "id": None
                }
            contacts_data[contact_name]["history"].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "healing_score": msg.get("healing_score", 0),
                "model": msg.get("model", "Unknown"),
                "sentiment": msg.get("sentiment", "Unknown"),
                "emotional_state": msg.get("emotional_state", "Unknown")
            })

        return contacts_data
    except Exception as e:
        st.warning(f"Could not load user data: {e}")
        return {}

# Data Saving with error logging
def save_contact(name, context, contact_id=None):
    user_id = get_current_user_id()
    if not supabase or not name.strip() or not user_id:
        st.error("Cannot save contact: User not logged in or invalid input.")
        return False
    if contact_id is None:
        response = supabase.table("contacts").select("id").eq("name", name).eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            st.error(f"A contact with the name '{name}' already exists for your account.")
            return False
    try:
        contact_data = {"name": name, "context": context, "user_id": user_id}
        if contact_id:
            result = supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
        else:
            contact_data["created_at"] = datetime.now(timezone.utc).isoformat()
            result = supabase.table("contacts").insert(contact_data).execute()
        if result.error:
            st.error(f"Error saving contact: {result.error.message}")
            return False
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Exception saving contact: {e}")
        return False

def delete_contact(contact_id):
    user_id = get_current_user_id()
    if not supabase or not contact_id or not user_id:
        st.error("Cannot delete contact: User not logged in or invalid input.")
        return False
    try:
        contact_name_data = supabase.table("contacts").select("name").eq("id", contact_id).eq("user_id", user_id).execute().data
        if contact_name_data:
            contact_name = contact_name_data[0]["name"]
            supabase.table("messages").delete().eq("contact_name", contact_name).eq("user_id", user_id).execute()
            if f"last_response_{contact_name}" in st.session_state:
                del st.session_state[f"last_response_{contact_name}"]
        supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error deleting contact: {e}")
        return False

def save_message(contact_name, message_type, original, result, emotional_state, healing_score, model_used, sentiment="Unknown"):
    user_id = get_current_user_id()
    if not supabase or not user_id:
        st.error("Cannot save message: User not logged in.")
        return False
    try:
        supabase.table("messages").insert({
            "contact_name": contact_name,
            "type": message_type,
            "original": original,
            "result": result,
            "emotional_state": emotional_state,
            "healing_score": healing_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model_used,
            "sentiment": sentiment,
            "user_id": user_id
        }).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving message: {e}")
        return False

# AI processing, UI, and main() functions remain the same as in your current code...
# For brevity, I assume you copy/paste your unchanged code from your existing app here.

# Just please remember to copy your current UI functions and other pieces below to complete the file!

# --- Main Application Flow ---
def main():
    def restore_session():
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                if not st.session_state.get("authenticated", False):
                    st.session_state.authenticated = True
                    st.session_state.user = session.user
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.app_mode = "contacts_list" if st.session_state.contacts else "first_time_setup"
        except Exception as e:
            st.error(f"Error restoring session: {e}")

    restore_session()
    st.set_page_config(page_title="The Third Voice", layout="wide")

    with st.sidebar:
        st.image("https://placehold.co/150x50/ADD8E6/000?text=The+Third+Voice+AI", use_container_width=True)
        st.title("The Third Voice AI")
        if st.session_state.authenticated:
            st.write(f"Logged in as: **{st.session_state.user.email}**")
            st.write(f"User ID: `{st.session_state.user.id}`")
            if st.button("Logout", use_container_width=True):
                sign_out()

        st.markdown("---")
        st.subheader("🚀 Debug Info (For Co-Founders Only)")
        if st.checkbox("Show Debug Details"):
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None

                debug_info = {
                    "Supabase Connected": "Yes" if session else "No",
                    "User ID": user.id if user else None,
                    "User Email": user.email if user else None,
                    "Session Expires At": session.expires_at if session else None,
                    "Access Token": session.access_token[:10] + "..." if session and session.access_token else None,
                    "Test Contacts Query": None,
                    "Streamlit Session State": dict(st.session_state),
                    "Environment Variables": {
                        "STREAMLIT_SERVER_PORT": os.getenv("STREAMLIT_SERVER_PORT"),
                    },
                    "Secrets Loaded": {
                        "Supabase URL": bool(st.secrets.get("supabase", {}).get("url")),
                        "Supabase Key": bool(st.secrets.get("supabase", {}).get("key")),
                        "OpenRouter API Key": bool(st.secrets.get("openrouter", {}).get("api_key")),
                    }
                }

                try:
                    test_contacts_query = supabase.table("contacts").select("id").limit(1).execute()
                    debug_info["Test Contacts Query"] = test_contacts_query.data if test_contacts_query.data else "No contacts found or RLS restricted."
                except Exception as e:
                    debug_info["Test Contacts Query"] = f"Test query failed: {e}"

                st.code(json.dumps(debug_info, indent=2, default=str), language="json")

            except Exception as e:
                st.error(f"Error generating debug info: {e}")

    # Page routing based on auth
    if st.session_state.authenticated:
        if st.session_state.app_mode == "first_time_setup":
            render_first_time_screen()
        elif st.session_state.app_mode == "contacts_list":
            render_contacts_list_view()
        elif st.session_state.app_mode == "conversation_view":
            render_conversation_view()
        elif st.session_state.app_mode == "edit_contact_view":
            render_edit_contact_view()
        elif st.session_state.app_mode == "add_contact_view":
            render_add_contact_view()
        else:
            st.session_state.app_mode = "contacts_list"
            st.experimental_rerun()
    else:
        if st.session_state.app_mode == "signup":
            signup_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
