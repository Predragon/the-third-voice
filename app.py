import streamlit as st
import datetime
import requests
from supabase import create_client, Client
import os
import json # For handling JSON data for contacts/messages if needed
from datetime import datetime, timezone # For timestamps

# --- Constants ---
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}

# AI Model Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-2-9b-it:free" # Your model name for OpenRouter

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

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "login" 

if 'contacts' not in st.session_state:
    st.session_state.contacts = {}
if 'active_contact' not in st.session_state:
    st.session_state.active_contact = None
if 'edit_contact' not in st.session_state:
    st.session_state.edit_contact = None
if 'conversation_input_text' not in st.session_state:
    st.session_state.conversation_input_text = ""
if 'clear_conversation_input' not in st.session_state:
    st.session_state.clear_conversation_input = False
if 'edit_contact_name_input' not in st.session_state:
    st.session_state.edit_contact_name_input = ""
if 'add_contact_name_input' not in st.session_state:
    st.session_state.add_contact_name_input = ""
if 'add_contact_context_select' not in st.session_state:
    st.session_state.add_contact_context_select = list(CONTEXTS.keys())[0]
if 'last_error_message' not in st.session_state:
    st.session_state.last_error_message = None

# --- Helper Functions ---
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
        st.warning(f"Error checking contact existence: {e}")
        return False

# --- Authentication ---
def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            st.success("Sign-up successful! Please check your email to confirm your account.")
            st.session_state.app_mode = "login"
            st.rerun()
        elif response.error:
            st.error(f"Sign-up failed: {response.error.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred during sign-up: {e}")

def sign_in(email, password):
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
    try:
        response = supabase.auth.sign_out()
        if not response.error:
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.contacts = {}
            st.session_state.active_contact = None
            st.session_state.edit_contact = None
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.edit_contact_name_input = ""
            st.session_state.add_contact_name_input = ""
            st.session_state.add_contact_context_select = list(CONTEXTS.keys())[0]
            st.session_state.last_error_message = None
            st.session_state.app_mode = "login"
            st.info("You have been logged out.")
            st.rerun()
        else:
            st.error(f"Logout failed: {response.error.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred during logout: {e}")

# --- Data Loading ---
@st.cache_data(ttl=60)
def load_contacts_and_history():
    user_id = get_current_user_id()
    if not supabase or not user_id:
        return {}
    try:
        contacts_response = supabase.table("contacts").select("*").eq("user_id", user_id).execute()
        contacts_data = {c["name"]: {
            "context": c["context"],
            "history": [],
            "created_at": c.get("created_at", datetime.now(timezone.utc).isoformat()),
            "id": c.get("id")
        } for c in contacts_response.data}

        messages_response = supabase.table("messages").select("*").eq("user_id", user_id).order("timestamp").execute()
        messages = messages_response.data

        for msg in messages:
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

# --- Data Saving ---
def save_contact(name, context, contact_id=None):
    user_id = get_current_user_id()
    if not supabase or not name.strip() or not user_id:
        st.error("Cannot save contact: User not logged in or invalid input.")
        return False
    if contact_id is None:
        # Check duplicate name in DB before insert
        if contact_exists_for_user(name, user_id):
            st.error(f"Contact with name '{name}' already exists for your account.")
            return False
    try:
        contact_data = {"name": name, "context": context, "user_id": user_id}
        if contact_id:
            supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
        else:
            contact_data["created_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("contacts").insert(contact_data).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
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

# --- AI Message Processing ---
def process_message(contact_name, message, context):
    st.session_state.last_error_message = None
    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty. Please type something to transform."
        return
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        st.session_state.last_error_message = "OpenRouter API Key not found in Streamlit secrets under [openrouter]. Please add it."
        return
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    system_prompt = (
        f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}. "
        f"{'Understand what they mean and suggest a loving response.' if is_incoming else 'Reframe their message to be constructive and loving.'} "
        "Keep it concise, insightful, and actionable (2-3 paragraphs)."
    )
    try:
        with st.spinner("🤖 Processing..."):
            headers = {
                "Authorization": f"Bearer {openrouter_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            response = requests.post(API_URL, headers=headers, json=payload, timeout=25).json()
            if "choices" in response and len(response["choices"]) > 0:
                ai_response_text = response["choices"][0]["message"]["content"].strip()
                ai_sentiment = "Neutral"
                ai_emotional_state = "Calm"
                healing_score = 5 + (1 if len(ai_response_text) > 200 else 0) + min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in ai_response_text.lower()))
                healing_score = min(10, healing_score)
            else:
                st.session_state.last_error_message = f"AI API response missing 'choices': {response}"
                return
        save_message(contact_name, "incoming", message, None, "Unknown", 0, "N/A")
        save_message(contact_name, mode, message, ai_response_text, ai_emotional_state, healing_score, MODEL, ai_sentiment)
        st.session_state[f"last_response_{contact_name}"] = {
            "response": ai_response_text,
            "healing_score": healing_score,
            "timestamp": datetime.now().timestamp(),
            "model": MODEL
        }
        st.session_state.clear_conversation_input = True
        st.rerun()
    except requests.exceptions.Timeout:
        st.session_state.last_error_message = "API request timed out. Please try again. The AI might be busy."
    except requests.exceptions.ConnectionError:
        st.session_state.last_error_message = "Connection error. Please check your internet connection."
    except requests.exceptions.RequestException as e:
        st.session_state.last_error_message = f"Network or API error: {e}. Please check your API key or connection."
    except (KeyError, IndexError) as e:
        st.session_state.last_error_message = f"Received an unexpected response from the AI API. Error: {e}"
    except Exception as e:
        st.session_state.last_error_message = f"An unexpected error occurred during AI processing: {e}"

# --- UI Pages ---

def login_page():
    st.title("Welcome to The Third Voice AI")
    st.subheader("Login to continue your healing journey.")
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login")
        if login_button:
            sign_in(email, password)
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account"):
        st.session_state.app_mode = "signup"
        st.rerun()

def signup_page():
    st.title("Create Your Third Voice AI Account")
    st.subheader("Start your journey towards healthier conversations.")
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        signup_button = st.form_submit_button("Sign Up")
        if signup_button:
            sign_up(email, password)
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login"):
        st.session_state.app_mode = "login"
        st.rerun()

def render_first_time_screen():
    st.markdown("### 🎙️ Welcome to The Third Voice")
    st.markdown("Choose a relationship type to get started, or add a custom contact:")
    cols = st.columns(2)
    contexts_items = list(CONTEXTS.items())
    for i, (context_key, context_info) in enumerate(contexts_items):
        with cols[i % 2]:
            if st.button(
                f"{context_info['icon']} {context_key.title()}\n{context_info['description']}",
                key=f"context_{context_key}",
                use_container_width=True
            ):
                default_names = {
                    "romantic": "Partner",
                    "coparenting": "Co-parent",
                    "workplace": "Colleague",
                    "family": "Family Member",
                    "friend": "Friend"
                }
                contact_name = default_names.get(context_key, context_key.title())
                if contact_name not in st.session_state.contacts:
                    if save_contact(contact_name, context_key):
                        st.session_state.contacts = load_contacts_and_history()
                        st.session_state.active_contact = contact_name
                        st.session_state.app_mode = "conversation_view"
                        st.rerun()
                else:
                    st.session_state.active_contact = contact_name
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()
    st.markdown("---")
    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name_input")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="first_time_new_contact_context_select")
        if st.form_submit_button("Add Custom Contact"):
            name_to_add = st.session_state.first_time_new_contact_name_input
            context_to_add = st.session_state.first_time_new_contact_context_select
            if name_to_add.strip():
                user_id = get_current_user_id()
                if user_id and not contact_exists_for_user(name_to_add, user_id):
                    if save_contact(name_to_add, context_to_add):
                        st.session_state.contacts = load_contacts_and_history()
                        st.session_state.active_contact = name_to_add
                        st.session_state.app_mode = "conversation_view"
                        st.rerun()
                    else:
                        st.session_state.last_error_message = "Failed to add contact. Please try again."
                else:
                    st.session_state.last_error_message = "Contact with this name already exists for your account."
                    st.rerun()
            else:
                st.session_state.last_error_message = "Contact name cannot be empty."
                st.rerun()

def render_contacts_list_view():
    st.markdown("### 🎙️ The Third Voice - Your Contacts")
    sorted_contacts = sorted(
        st.session_state.contacts.items(),
        key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"],
        reverse=True
    )
    for name, data in sorted_contacts:
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start chatting!"
        time_str = last_msg["time"] if last_msg else "New"
        if st.button(
            f"**{name}** | {time_str}\n"
            f"_{preview}_",
            key=f"contact_{name}",
            use_container_width=True
        ):
            st.session_state.active_contact = name
            st.session_state.app_mode = "conversation_view"
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.app_mode = "add_contact_view"
        st.rerun()

def render_edit_contact_view():
    if not st.session_state.edit_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    contact = st.session_state.edit_contact
    st.markdown(f"### ✏️ Edit Contact: {contact['name']}")
    if st.button("← Back", key="back_to_conversation", use_container_width=True):
        st.session_state.app_mode = "conversation_view"
        st.session_state.edit_contact = None
        st.session_state.last_error_message = None
        st.session_state.clear_conversation_input = False
        st.rerun()
    if "edit_contact_name_input" not in st.session_state or st.session_state.edit_contact_name_input == "":
        st.session_state.edit_contact_name_input = contact["name"]
    elif st.session_state.edit_contact_name_input != contact["name"] and st.session_state.edit_contact_name_input == st.session_state.get('initial_edit_contact_name', ''):
        st.session_state.edit_contact_name_input = contact["name"]
    if 'initial_edit_contact_name' not in st.session_state:
        st.session_state.initial_edit_contact_name = contact["name"]
    elif st.session_state.initial_edit_contact_name != contact["name"]:
        st.session_state.initial_edit_contact_name = contact["name"]
        st.session_state.edit_contact_name_input = contact["name"]
    with st.form("edit_contact_form"):
        name_input = st.text_input("Name",
                                   value=st.session_state.edit_contact_name_input,
                                   key="edit_contact_name_input_widget")
        context_options = list(CONTEXTS.keys())
        initial_context_index = context_options.index(contact["context"]) if contact["context"] in context_options else 0
        context = st.selectbox("Relationship", context_options,
                               index=initial_context_index,
                               format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
                               key="edit_contact_context_select")
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                new_name = st.session_state.edit_contact_name_input_widget
                new_context = st.session_state.edit_contact_context_select
                if not new_name.strip():
                    st.error("Contact name cannot be empty.")
                    st.rerun()
                if new_name != contact["name"]:
                    user_id = get_current_user_id()
                    if user_id and contact_exists_for_user(new_name, user_id):
                        st.error(f"Contact with name '{new_name}' already exists for your account.")
                        st.rerun()
                if save_contact(new_name, new_context, contact["id"]):
                    st.success(f"Updated {new_name}")
                    if st.session_state.active_contact == contact["name"]:
                        st.session_state.active_contact = new_name
                    st.session_state.app_mode = "conversation_view"
                    st.session_state.edit_contact = None
                    st.session_state.last_error_message = None
                    st.session_state.edit_contact_name_input = ""
                    st.session_state.initial_edit_contact_name = ""
                    st.session_state.clear_conversation_input = False
                    st.rerun()
        with col2:
            if st.form_submit_button("🗑️ Delete Contact"):
                if delete_contact(contact["id"]):
                    st.success(f"Deleted contact: {contact['name']}")
                    st.session_state.app_mode = "contacts_list"
                    st.session_state.active_contact = None
                    st.session_state.edit_contact = None
                    st.session_state.last_error_message = None
                    st.session_state.clear_conversation_input = False
                    st.rerun()

def render_conversation_view():
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    back_col, edit_col, _ = st.columns([2, 2, 6])
    with back_col:
        if st.button("← Back", key="back_btn", use_container_width=True):
            st.session_state.app_mode = "contacts_list"
            st.session_state.active_contact = None
            st.session_state.last_error_message = None
            st.session_state.clear_conversation_input = False
            st.rerun()
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            st.session_state.edit_contact_name_input = contact_name
            st.session_state.initial_edit_contact_name = contact_name
            st.session_state.app_mode = "edit_contact_view"
            st.session_state.last_error_message = None
            st.session_state.clear_conversation_input = False
            st.rerun()
    st.markdown("---")
    st.markdown("#### 💭 Your Input")
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    user_input_area = st.text_area(
        "What's happening?",
        value=input_value,
        key="conversation_input_text",
        placeholder="Share their message or your response...",
        height=120
    )
    if st.session_state.clear_conversation_input:
        st.session_state.clear_conversation_input = False
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", use_container_width=True):
            input_message = st.session_state.conversation_input_text
            process_message(contact_name, input_message, context)
    with col2:
        if st.button("🗑️️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    st.markdown("---")
    st.markdown("#### 🤖 AI Response")
    last_response_key = f"last_response_{contact_name}"
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            with st.container():
                st.markdown("**AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                col_score, col_model = st.columns([1, 1])
                with col_score:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Healing Score: {last_resp['healing_score']}/10")
                    else:
                        st.info(f"💡 Healing Score: {last_resp['healing_score']}/10")
                with col_model:
                    st.caption(f"🤖 Model: {last_resp.get('model', 'Unknown')}")
                if last_resp["healing_score"] >= 8:
                    st.balloons()
        else:
            del st.session_state[last_response_key]
            st.info("💭 Your AI response will appear here after you click Transform")
    else:
        st.info("💭 Your AI response will appear here after you click Transform")
    st.markdown("---")
    st.markdown("#### 📜 Conversation History")
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total)")
        with st.expander("View Chat History", expanded=False):
            for msg in reversed(history[-10:]):
                st.markdown(f"""
                **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                """)
                with st.container():
                    st.markdown("**Your Message:**")
                    st.info(msg['original'])
                with st.container():
                    st.markdown("**AI Guidance:**")
                    st.text_area(
                        "AI Guidance for History Entry",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg['id']}",
                        disabled=True,
                        label_visibility="hidden"
                    )
                    st.caption(f"🤖 Model: {msg.get('model', 'Unknown')}")
                st.markdown("---")
    else:
        st.info("📝 No chat history yet. Start a conversation above!")

def render_add_contact_view():
    st.markdown("### ➕ Add New Contact")
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        st.session_state.app_mode = "contacts_list"
        st.session_state.last_error_message = None
        st.session_state.clear_conversation_input = False
        st.rerun()
    with st.form("add_contact_form"):
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="add_contact_name_input_widget")
        context_options = list(CONTEXTS.keys())
        context_selected_index = context_options.index(st.session_state.add_contact_context_select) if st.session_state.add_contact_context_select in context_options else 0
        context = st.selectbox("Relationship", context_options,
                               index=context_selected_index,
                               format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
                               key="add_contact_context_select_widget")
        if st.form_submit_button("Add Contact"):
            name_to_add = st.session_state.add_contact_name_input_widget
            context_to_add = st.session_state.add_contact_context_select_widget
            if name_to_add.strip():
                user_id = get_current_user_id()
                if user_id and not contact_exists_for_user(name_to_add, user_id):
                    if save_contact(name_to_add, context_to_add):
                        st.session_state.contacts = load_contacts_and_history() 
                        st.success(f"Added {name_to_add}")
                        st.session_state.app_mode = "contacts_list"
                        st.session_state.add_contact_name_input = ""
                        st.session_state.add_contact_context_select = list(CONTEXTS.keys())[0]
                        st.session_state.last_error_message = None
                        st.session_state.clear_conversation_input = False
                        st.rerun()
                    else:
                        st.session_state.last_error_message = "Failed to add contact. Please try again."
                else:
                    st.session_state.last_error_message = "Contact with this name already exists for your account."
                    st.rerun()
            else:
                st.session_state.last_error_message = "Contact name cannot be empty."
                st.rerun()

# --- Main ---
def main():
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
            st.write("### 🔑 Supabase Connection Status:")
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None
                if session:
                    st.success("Supabase connected and user session active!")
                    st.write(f"**User ID:** `{user.id if user else 'N/A'}`")
                    st.write(f"**User Email:** `{user.email if user else 'N/A'}`")
                    st.write(f"**Session Expires At:** `{session.expires_at}`")
                    st.write(f"**Access Token (Truncated):** `{session.access_token[:10]}...`")
                else:
                    st.warning("Supabase connected, but no active user session.")
                    st.write("User needs to log in.")
                st.write("Attempting a test query (respects RLS if enabled)...")
                try:
                    test_contacts_query = supabase.table("contacts").select("id").limit(1).execute()
                    st.write(f"Test query result: {test_contacts_query.data if test_contacts_query.data else 'No contacts found or RLS restricted.'}")
                except Exception as e:
                    st.error(f"Test query failed: {e}")
            except Exception as e:
                st.error(f"Supabase connection or authentication error: {e}")
                st.write("Please ensure `[supabase] url` and `[supabase] key` are set in Streamlit Cloud App Secrets.")
            st.write("### 💾 Streamlit Session State:")
            st.json(st.session_state.to_dict())
            st.write("### 🌐 Environment Variables (Limited View):")
            env_vars_to_show = {"STREAMLIT_SERVER_PORT": os.getenv("STREAMLIT_SERVER_PORT")}
            st.json(env_vars_to_show)
            st.write("### 📜 Streamlit Secrets (Accessible via code):")
            st.write(f"Supabase URL: `{'*' * 5} (loaded)`")
            st.write(f"Supabase Key: `{'*' * 5} (loaded)`")
            st.write(f"OpenRouter API Key: `{'*' * 5} (loaded)`")
            if not st.secrets.get("supabase", {}).get("url"):
                st.error("Supabase URL secret is missing or empty under [supabase]!")
            if not st.secrets.get("supabase", {}).get("key"):
                st.error("Supabase Key secret is missing or empty under [supabase]!")
            if not st.secrets.get("openrouter", {}).get("api_key"):
                st.error("OpenRouter API Key secret is missing or empty under [openrouter]!")
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
            st.rerun()
    else:
        if st.session_state.app_mode == "signup":
            signup_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
