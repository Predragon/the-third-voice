import streamlit as st
import datetime
import aiohttp
import asyncio
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

# AI Model Configuration
API_URL = st.secrets.get("openrouter", {}).get("api_url", "https://openrouter.ai/api/v1/chat/completions")
MODEL = st.secrets.get("openrouter", {}).get("model", "google/gemma-2-9b-it:free")
API_TIMEOUT = st.secrets.get("openrouter", {}).get("timeout", 30)

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
def init_session_state():
    defaults = {
        "authenticated": False,
        "user": None,
        "app_mode": "login",
        "contacts": {},
        "active_contact": None,
        "edit_contact": None,
        "conversation_input_text": "",
        "clear_conversation_input": False,
        "edit_contact_name_input": "",
        "add_contact_name_input": "",
        "add_contact_context_select": list(CONTEXTS.keys())[0],
        "last_error_message": None,
        "last_responses": {},
        "history_page": 1
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- Helper Functions ---
def get_current_user_id():
    try:
        session = supabase.auth.get_session()
        return session.user.id if session and session.user else None
    except Exception as e:
        st.error(f"Error getting user session: {e}")
        return None

def validate_input(text, max_length=100, field="input"):
    if not text.strip():
        st.session_state.last_error_message = f"{field} cannot be empty."
        return False
    if len(text) > max_length:
        st.session_state.last_error_message = f"{field} cannot exceed {max_length} characters."
        return False
    if not all(c.isalnum() or c.isspace() or c in ".-_" for c in text):
        st.session_state.last_error_message = f"{field} can only contain letters, numbers, spaces, periods, hyphens, or underscores."
        return False
    return True

def handle_error(e, context="Operation"):
    st.session_state.last_error_message = f"{context} failed: {e}"
    return False

# --- Authentication Functions ---
def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            st.success("Sign-up successful! Please check your email to confirm your account.")
            st.session_state.app_mode = "login"
        elif response.error:
            st.session_state.last_error_message = f"Sign-up failed: {response.error.message}"
    except Exception as e:
        handle_error(e, "Sign-up")

def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.update({
                "authenticated": True,
                "user": response.user,
                "contacts": load_contacts_and_history(get_current_user_id()),
                "app_mode": "contacts_list" if load_contacts_and_history(get_current_user_id()) else "first_time_setup",
                "last_error_message": None
            })
            st.success(f"Welcome back, {response.user.email}!")
        elif response.error:
            st.session_state.last_error_message = f"Login failed: {response.error.message}"
    except Exception as e:
        handle_error(e, "Login")

def sign_out():
    try:
        supabase.auth.sign_out()
        st.session_state.update({
            "authenticated": False,
            "user": None,
            "contacts": {},
            "active_contact": None,
            "edit_contact": None,
            "conversation_input_text": "",
            "clear_conversation_input": False,
            "edit_contact_name_input": "",
            "add_contact_name_input": "",
            "add_contact_context_select": list(CONTEXTS.keys())[0],
            "last_error_message": None,
            "last_responses": {},
            "app_mode": "login"
        })
        st.info("You have been logged out.")
    except Exception as e:
        handle_error(e, "Logout")

# --- Data Loading Functions ---
@st.experimental_memo(ttl=30)
def load_contacts_and_history(_user_id, page=1, page_size=50):
    if not supabase or not _user_id:
        return {}
    try:
        response = supabase.rpc("get_user_contacts_and_messages", {
            "user_id": _user_id,
            "page_size": page_size,
            "page_offset": (page - 1) * page_size
        }).execute()
        contacts_data = {}
        for row in response.data:
            contact_name = row["contact_name"]
            if contact_name not in contacts_data:
                contacts_data[contact_name] = {
                    "context": row["context"],
                    "history": [],
                    "created_at": row["created_at"],
                    "id": row["contact_id"]
                }
            if row["message_id"]:
                contacts_data[contact_name]["history"].append({
                    "id": f"{row['message_type']}_{row['timestamp']}",
                    "time": datetime.fromisoformat(row["timestamp"]).strftime("%m/%d %H:%M"),
                    "type": row["message_type"],
                    "original": row["original"],
                    "result": row["result"] or "",
                    "healing_score": row["healing_score"] or 0,
                    "model": row["model"] or "Unknown",
                    "sentiment": row["sentiment"] or "Unknown",
                    "emotional_state": row["emotional_state"] or "Unknown"
                })
        return contacts_data
    except Exception as e:
        st.warning(f"Could not load user data: {e}")
        return {}

# --- Data Saving Functions ---
def save_contact(name, context, contact_id=None):
    user_id = get_current_user_id()
    if not supabase or not name.strip() or not user_id:
        return handle_error("Invalid input or user not logged in", "Save contact")
    if not validate_input(name, field="Contact name"):
        return False
    try:
        contact_data = {"name": name, "context": context, "user_id": user_id}
        if contact_id:
            supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
        else:
            contact_data["created_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("contacts").insert(contact_data).execute()
        st.session_state.last_error_message = None
        return True
    except Exception as e:
        if "duplicate key" in str(e).lower():
            st.session_state.last_error_message = f"Contact '{name}' already exists."
        else:
            handle_error(e, "Save contact")
        return False

def delete_contact(contact_id):
    user_id = get_current_user_id()
    if not supabase or not contact_id or not user_id:
        return handle_error("Invalid input or user not logged in", "Delete contact")
    try:
        contact_name_data = supabase.table("contacts").select("name").eq("id", contact_id).eq("user_id", user_id).execute().data
        if contact_name_data:
            contact_name = contact_name_data[0]["name"]
            supabase.table("messages").delete().eq("contact_name", contact_name).eq("user_id", user_id).execute()
            if contact_name in st.session_state.last_responses:
                del st.session_state.last_responses[contact_name]
        supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
        st.session_state.last_error_message = None
        return True
    except Exception as e:
        handle_error(e, "Delete contact")
        return False

def save_message(contact_name, message_type, original, result, emotional_state, healing_score, model_used, sentiment="Unknown", is_last_response=False):
    user_id = get_current_user_id()
    if not supabase or not user_id:
        return handle_error("User not logged in", "Save message")
    try:
        if is_last_response:
            supabase.table("messages").update({"is_last_response": False}).eq("contact_name", contact_name).eq("user_id", user_id).execute()
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
            "user_id": user_id,
            "is_last_response": is_last_response
        }).execute()
        st.session_state.last_error_message = None
        return True
    except Exception as e:
        handle_error(e, "Save message")
        return False

# --- AI Message Processing ---
@st.experimental_memo(ttl=3600)
def get_cached_ai_response(_contact_name, _message, _context):
    try:
        response = supabase.table("ai_response_cache").select("response, healing_score, model, sentiment, emotional_state")\
            .eq("contact_name", _contact_name).eq("message", _message).eq("context", _context).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None

async def fetch_ai_response(session, headers, payload):
    async with session.post(API_URL, headers=headers, json=payload, timeout=API_TIMEOUT) as response:
        return await response.json()

def process_message(contact_name, message, context):
    if not validate_input(message, max_length=500, field="Message"):
        return
    cached_response = get_cached_ai_response(contact_name, message, context)
    if cached_response:
        st.session_state.last_responses[contact_name] = {
            "response": cached_response["response"],
            "healing_score": cached_response["healing_score"],
            "timestamp": datetime.now().timestamp(),
            "model": cached_response["model"]
        }
        save_message(contact_name, "incoming", message, None, "Unknown", 0, "N/A")
        save_message(contact_name, "translate" if any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"]) else "coach",
                    message, cached_response["response"], cached_response["emotional_state"], cached_response["healing_score"],
                    cached_response["model"], cached_response["sentiment"], is_last_response=True)
        st.session_state.clear_conversation_input = True
        return

    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        st.session_state.last_error_message = "OpenRouter API Key not found."
        return

    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    system_prompt = (
        f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}. "
        f"{'Understand what they mean and suggest a loving response.' if is_incoming else 'Reframe their message to be constructive and loving.'} "
        "Keep it concise, insightful, and actionable (2-3 paragraphs)."
    )
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

    async def try_fetch():
        async with aiohttp.ClientSession() as session:
            for attempt in range(3):
                try:
                    response = await fetch_ai_response(session, headers, payload)
                    if "choices" in response and response["choices"]:
                        ai_response_text = response["choices"][0]["message"]["content"].strip()
                        healing_score = 5 + (1 if len(ai_response_text) > 200 else 0) + \
                                       min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in ai_response_text.lower()))
                        healing_score = min(10, healing_score)
                        supabase.table("ai_response_cache").insert({
                            "contact_name": contact_name,
                            "message": message,
                            "context": context,
                            "response": ai_response_text,
                            "healing_score": healing_score,
                            "model": MODEL,
                            "sentiment": "Neutral",
                            "emotional_state": "Calm",
                            "user_id": get_current_user_id()
                        }).execute()
                        return ai_response_text, healing_score
                    else:
                        st.session_state.last_error_message = f"Invalid AI response: {response}"
                        return None, None
                except aiohttp.ClientError as e:
                    if attempt == 2:
                        st.session_state.last_error_message = f"API error after retries: {e}"
                        return None, None
                    await asyncio.sleep(2 ** attempt)

    with st.spinner("🤖 Processing..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ai_response_text, healing_score = loop.run_until_complete(try_fetch())
        loop.close()

    if ai_response_text:
        st.session_state.last_responses[contact_name] = {
            "response": ai_response_text,
            "healing_score": healing_score,
            "timestamp": datetime.now().timestamp(),
            "model": MODEL
        }
        save_message(contact_name, "incoming", message, None, "Unknown", 0, "N/A")
        save_message(contact_name, mode, message, ai_response_text, "Calm", healing_score, MODEL, "Neutral", is_last_response=True)
        st.session_state.clear_conversation_input = True
        st.session_state.last_error_message = None

# --- UI Pages ---
def login_page():
    st.title("Welcome to The Third Voice AI")
    st.subheader("Login to continue your healing journey.")
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        def handle_login_submit():
            sign_in(email, password)
        st.form_submit_button("Login", on_submit=handle_login_submit)
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account"):
        st.session_state.app_mode = "signup"

def signup_page():
    st.title("Create Your Third Voice AI Account")
    st.subheader("Start your journey towards healthier conversations.")
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        def handle_signup_submit():
            sign_up(email, password)
        st.form_submit_button("Sign Up", on_submit=handle_signup_submit)
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login"):
        st.session_state.app_mode = "login"

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
                if save_contact(contact_name, context_key):
                    st.session_state.update({
                        "contacts": load_contacts_and_history(get_current_user_id()),
                        "active_contact": contact_name,
                        "app_mode": "conversation_view",
                        "last_error_message": None
                    })
                    st.rerun()
    st.markdown("---")
    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name_input")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="first_time_new_contact_context_select")
        def handle_first_time_contact_submit():
            name_to_add = st.session_state.first_time_new_contact_name_input
            context_to_add = st.session_state.first_time_new_contact_context_select
            if name_to_add.strip() and save_contact(name_to_add, context_to_add):
                st.session_state.update({
                    "contacts": load_contacts_and_history(get_current_user_id()),
                    "active_contact": name_to_add,
                    "app_mode": "conversation_view",
                    "last_error_message": None
                })
                st.success(f"Added {name_to_add}")
        st.form_submit_button("Add Custom Contact", on_submit=handle_first_time_contact_submit)

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
            st.session_state.update({
                "active_contact": name,
                "app_mode": "conversation_view",
                "conversation_input_text": "",
                "clear_conversation_input": False,
                "last_error_message": None
            })
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        st.session_state.app_mode = "add_contact_view"

def render_edit_contact_view():
    if not st.session_state.edit_contact:
        st.session_state.app_mode = "contacts_list"
        return
    contact = st.session_state.edit_contact
    st.markdown(f"### ✏️ Edit Contact: {contact['name']}")
    if st.button("← Back", key="back_to_conversation", use_container_width=True):
        st.session_state.update({
            "app_mode": "conversation_view",
            "edit_contact": None,
            "last_error_message": None,
            "clear_conversation_input": False
        })
    if "edit_contact_name_input" not in st.session_state or st.session_state.edit_contact_name_input == "":
        st.session_state.edit_contact_name_input = contact["name"]
    with st.form("edit_contact_form"):
        name_input = st.text_input("Name", value=st.session_state.edit_contact_name_input, key="edit_contact_name_input_widget")
        context_options = list(CONTEXTS.keys())
        initial_context_index = context_options.index(contact["context"]) if contact["context"] in context_options else 0
        context = st.selectbox("Relationship", context_options, index=initial_context_index, format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="edit_contact_context_select")
        col1, col2 = st.columns(2)
        def handle_edit_contact_submit():
            new_name = st.session_state.edit_contact_name_input_widget
            new_context = st.session_state.edit_contact_context_select
            if not new_name.strip():
                st.session_state.last_error_message = "Contact name cannot be empty."
                return
            if save_contact(new_name, new_context, contact["id"]):
                st.session_state.update({
                    "active_contact": new_name if st.session_state.active_contact == contact["name"] else st.session_state.active_contact,
                    "app_mode": "conversation_view",
                    "edit_contact": None,
                    "last_error_message": None,
                    "edit_contact_name_input": "",
                    "clear_conversation_input": False,
                    "contacts": load_contacts_and_history(get_current_user_id())
                })
                st.success(f"Updated {new_name}")
        def handle_delete_contact_submit():
            if st.checkbox("Confirm deletion", key="confirm_delete"):
                if delete_contact(contact["id"]):
                    st.session_state.update({
                        "app_mode": "contacts_list",
                        "active_contact": None,
                        "edit_contact": None,
                        "last_error_message": None,
                        "clear_conversation_input": False,
                        "contacts": load_contacts_and_history(get_current_user_id())
                    })
                    st.success(f"Deleted contact: {contact['name']}")
        with col1:
            st.form_submit_button("💾 Save Changes", on_submit=handle_edit_contact_submit)
        with col2:
            st.form_submit_button("🗑️ Delete Contact", on_submit=handle_delete_contact_submit)

def render_conversation_view():
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
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
            st.session_state.update({
                "app_mode": "contacts_list",
                "active_contact": None,
                "last_error_message": None,
                "clear_conversation_input": False
            })
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.update({
                "edit_contact": {"id": contact_id, "name": contact_name, "context": context},
                "edit_contact_name_input": contact_name,
                "app_mode": "edit_contact_view",
                "last_error_message": None,
                "clear_conversation_input": False
            })
    st.markdown("---")
    st.markdown("#### 💭 Your Input")
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    st.text_area(
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
            process_message(contact_name, st.session_state.conversation_input_text, context)
    with col2:
        if st.button("🗑️️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.update({
                "conversation_input_text": "",
                "clear_conversation_input": False,
                "last_error_message": None
            })
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    st.markdown("---")
    st.markdown("#### 🤖 AI Response")
    last_response_key = f"last_response_{contact_name}"
    if last_response_key in st.session_state.last_responses:
        last_resp = st.session_state.last_responses[last_response_key]
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
        response = supabase.table("messages").select("*").eq("contact_name", contact_name)\
            .eq("user_id", get_current_user_id()).eq("is_last_response", True).execute()
        if response.data:
            last_resp = response.data[0]
            st.session_state.last_responses[contact_name] = {
                "response": last_resp["result"],
                "healing_score": last_resp["healing_score"],
                "timestamp": datetime.fromisoformat(last_resp["timestamp"]).timestamp(),
                "model": last_resp["model"]
            }
            with st.container():
                st.markdown("**AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp["result"],
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
            st.info("💭 Your AI response will appear here after you click Transform")
    st.markdown("---")
    st.markdown("#### 📜 Conversation History")
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total)")
        with st.expander("View Chat History", expanded=False):
            for msg in reversed(history[-5:]):
                st.write_stream(f"""
                **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                **Your Message:** {msg['original']}
                **AI Guidance:** {msg['result']}
                🤖 Model: {msg.get('model', 'Unknown')}
                ---
                """)
            if len(history) > 5:
                if st.button("Load More", key=f"load_more_{contact_name}"):
                    st.session_state.history_page += 1
                    st.session_state.contacts = load_contacts_and_history(get_current_user_id(), page=st.session_state.history_page)
                    st.rerun()
    else:
        st.info("📝 No chat history yet. Start a conversation above!")

def render_add_contact_view():
    st.markdown("### ➕ Add New Contact")
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        st.session_state.update({
            "app_mode": "contacts_list",
            "last_error_message": None,
            "clear_conversation_input": False
        })
    with st.form("add_contact_form"):
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="add_contact_name_input_widget")
        context_options = list(CONTEXTS.keys())
        context_selected_index = context_options.index(st.session_state.add_contact_context_select) if st.session_state.add_contact_context_select in context_options else 0
        context = st.selectbox("Relationship", context_options, index=context_selected_index, format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="add_contact_context_select_widget")
        def handle_add_contact_submit():
            name_to_add = st.session_state.add_contact_name_input_widget
            context_to_add = st.session_state.add_contact_context_select_widget
            if name_to_add.strip() and save_contact(name_to_add, context_to_add):
                st.session_state.update({
                    "contacts": load_contacts_and_history(get_current_user_id()),
                    "app_mode": "contacts_list",
                    "add_contact_name_input": "",
                    "add_contact_context_select": list(CONTEXTS.keys())[0],
                    "last_error_message": None,
                    "clear_conversation_input": False
                })
                st.success(f"Added {name_to_add}")
        st.form_submit_button("Add Contact", on_submit=handle_add_contact_submit)

# --- Main Application Flow ---
def main():
    init_session_state()
    def restore_session():
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                if session.expires_at and session.expires_at < datetime.now(timezone.utc).timestamp():
                    st.session_state.update({
                        "authenticated": False,
                        "app_mode": "login",
                        "last_error_message": "Session expired. Please log in again."
                    })
                else:
                    st.session_state.update({
                        "authenticated": True,
                        "user": session.user,
                        "contacts": load_contacts_and_history(session.user.id),
                        "app_mode": "contacts_list" if load_contacts_and_history(session.user.id) else "first_time_setup"
                    })
            else:
                st.session_state.authenticated = False
                st.session_state.app_mode = "login"
        except Exception as e:
            handle_error(e, "Session restoration")
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
            debug_info = {
                "Supabase Connected": "Yes" if supabase.auth.get_session() else "No",
                "User ID": st.session_state.user.id if st.session_state.user else None,
                "User Email": st.session_state.user.email if st.session_state.user else None,
                "Contacts Count": len(st.session_state.contacts),
                "Secrets Loaded": {
                    "Supabase URL": bool(st.secrets.get("supabase", {}).get("url")),
                    "Supabase Key": bool(st.secrets.get("supabase", {}).get("key")),
                    "OpenRouter API Key": bool(st.secrets.get("openrouter", {}).get("api_key"))
                }
            }
            st.code(json.dumps(debug_info, indent=2, default=str), language="json")

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
    else:
        if st.session_state.app_mode == "signup":
            signup_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
