import streamlit as st
import requests
from supabase import create_client, Client
import os
import json
import hashlib
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
        'last_error_message': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Helper Functions ---
def get_current_user_id():
    """Get the current authenticated user's ID"""
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user.id
        return None
    except Exception as e:
        st.error(f"Error getting user session: {e}")
        return None

def create_message_hash(message, context):
    """Create a hash for message caching"""
    return hashlib.md5(f"{message.strip().lower()}{context}".encode()).hexdigest()

# --- Authentication Functions ---
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

# --- Data Loading Functions ---
@st.cache_data(ttl=30)  # Shorter cache time for more responsive updates
def load_contacts_and_history():
    user_id = get_current_user_id()
    if not user_id:
        return {}
    
    try:
        # Load contacts
        contacts_response = supabase.table("contacts").select("*").eq("user_id", user_id).execute()
        contacts_data = {}
        
        for contact in contacts_response.data:
            contacts_data[contact["name"]] = {
                "id": contact["id"],
                "context": contact["context"],
                "created_at": contact["created_at"],
                "history": []
            }
        
        # Load messages
        messages_response = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at").execute()
        
        for msg in messages_response.data:
            contact_name = msg["contact_name"]
            if contact_name in contacts_data:
                # Fix the datetime parsing issue
                msg_time = datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
                contacts_data[contact_name]["history"].append({
                    "id": msg["id"],
                    "time": msg_time.strftime("%m/%d %H:%M"),
                    "type": msg["type"],
                    "original": msg["original"],
                    "result": msg["result"],
                    "healing_score": msg.get("healing_score", 0),
                    "model": msg.get("model", "Unknown"),
                    "sentiment": msg.get("sentiment", "unknown"),
                    "emotional_state": msg.get("emotional_state", "unknown")
                })
        
        return contacts_data
        
    except Exception as e:
        st.warning(f"Could not load user data: {e}")
        return {}

# --- Data Saving Functions ---
def save_contact(name, context, contact_id=None):
    user_id = get_current_user_id()
    if not user_id or not name.strip():
        st.error("Cannot save contact: User not logged in or invalid input.")
        return False
    
    try:
        contact_data = {
            "name": name.strip(),
            "context": context,
            "user_id": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if contact_id:
            # Update existing contact
            response = supabase.table("contacts").update(contact_data).eq("id", contact_id).eq("user_id", user_id).execute()
        else:
            # Create new contact
            contact_data["created_at"] = datetime.now(timezone.utc).isoformat()
            response = supabase.table("contacts").insert(contact_data).execute()
        
        if response.data:
            st.cache_data.clear()
            return True
        else:
            st.error("Failed to save contact")
            return False
            
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            st.error(f"A contact with the name '{name}' already exists.")
        else:
            st.error(f"Error saving contact: {e}")
        return False

def delete_contact(contact_id):
    user_id = get_current_user_id()
    if not user_id or not contact_id:
        st.error("Cannot delete contact: User not logged in or invalid input.")
        return False
    
    try:
        # Get contact info first
        contact_response = supabase.table("contacts").select("name").eq("id", contact_id).eq("user_id", user_id).execute()
        
        if contact_response.data:
            contact_name = contact_response.data[0]["name"]
            
            # Delete the contact (messages will be cascade deleted due to FK constraint)
            supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
            
            # Clear any cached responses
            if f"last_response_{contact_name}" in st.session_state:
                del st.session_state[f"last_response_{contact_name}"]
            
            st.cache_data.clear()
            return True
        else:
            st.error("Contact not found")
            return False
            
    except Exception as e:
        st.error(f"Error deleting contact: {e}")
        return False

def save_message(contact_id, contact_name, message_type, original, result, emotional_state, healing_score, model_used, sentiment="unknown"):
    user_id = get_current_user_id()
    if not user_id:
        st.error("Cannot save message: User not logged in.")
        return False
    
    try:
        message_data = {
            "contact_id": contact_id,
            "contact_name": contact_name,
            "type": message_type,
            "original": original,
            "result": result,
            "emotional_state": emotional_state,
            "healing_score": healing_score,
            "model": model_used,
            "sentiment": sentiment,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("messages").insert(message_data).execute()
        
        if response.data:
            st.cache_data.clear()
            return True
        else:
            st.error("Failed to save message")
            return False
            
    except Exception as e:
        st.error(f"Error saving message: {e}")
        return False

# --- AI Message Processing ---
def process_message(contact_name, message, context):
    st.session_state.last_error_message = None
    
    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty. Please type something to transform."
        return
    
    # Get contact info
    contact_data = st.session_state.contacts.get(contact_name)
    if not contact_data:
        st.session_state.last_error_message = "Contact not found."
        return
    
    contact_id = contact_data["id"]
    
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        st.session_state.last_error_message = "OpenRouter API Key not found in Streamlit secrets under [openrouter]. Please add it."
        return
    
    # Determine message type
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    
    # Check cache first
    message_hash = create_message_hash(message, context)
    user_id = get_current_user_id()
    
    try:
        cache_response = supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", datetime.now(timezone.utc).isoformat()).execute()
        
        if cache_response.data:
            # Use cached response
            cached = cache_response.data[0]
            ai_response_text = cached["response"]
            healing_score = cached["healing_score"]
            ai_sentiment = cached["sentiment"]
            ai_emotional_state = cached["emotional_state"]
            
            st.info("Using cached response for faster processing")
        else:
            # Generate new response
            system_prompt = (
                f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}. "
                f"{'Understand what they mean and suggest a loving response.' if is_incoming else 'Reframe their message to be constructive and loving.'} "
                "Keep it concise, insightful, and actionable (2-3 paragraphs)."
            )
            
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
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
                response_json = response.json()
                
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    ai_response_text = response_json["choices"][0]["message"]["content"].strip()
                    ai_sentiment = "neutral"
                    ai_emotional_state = "calm"
                    
                    # Calculate healing score
                    healing_score = 5 + (1 if len(ai_response_text) > 200 else 0) + min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in ai_response_text.lower()))
                    healing_score = min(10, healing_score)
                    
                    # Cache the response
                    try:
                        cache_data = {
                            "contact_id": contact_id,
                            "message_hash": message_hash,
                            "context": context,
                            "response": ai_response_text,
                            "healing_score": healing_score,
                            "model": MODEL,
                            "sentiment": ai_sentiment,
                            "emotional_state": ai_emotional_state,
                            "user_id": user_id
                        }
                        supabase.table("ai_response_cache").insert(cache_data).execute()
                    except Exception as cache_error:
                        # Cache failure shouldn't stop the process
                        st.warning(f"Could not cache response: {cache_error}")
                    
                else:
                    st.session_state.last_error_message = f"AI API response missing 'choices': {response_json}"
                    return
        
        # Save the incoming message
        save_message(contact_id, contact_name, "incoming", message, None, "unknown", 0, "N/A")
        
        # Save the AI response
        save_message(contact_id, contact_name, mode, message, ai_response_text, ai_emotional_state, healing_score, MODEL, ai_sentiment)
        
        # Store response for immediate display
        st.session_state[f"last_response_{contact_name}"] = {
            "response": ai_response_text,
            "healing_score": healing_score,
            "timestamp": datetime.now().timestamp(),
            "model": MODEL
        }
        
        st.session_state.clear_conversation_input = True
        st.rerun()
        
    except requests.exceptions.Timeout:
        st.session_state.last_error_message = "API request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        st.session_state.last_error_message = "Connection error. Please check your internet connection."
    except requests.exceptions.RequestException as e:
        st.session_state.last_error_message = f"Network error: {e}"
    except Exception as e:
        st.session_state.last_error_message = f"An unexpected error occurred: {e}"

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
                
                if save_contact(contact_name, context_key):
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.active_contact = contact_name
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()
    
    st.markdown("---")
    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name_input")
        context = st.selectbox("Relationship", list(CONTEXTS.keys()), format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", key="first_time_new_contact_context_select")
        
        if st.form_submit_button("Add Custom Contact"):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.active_contact = name.strip()
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()
            else:
                st.error("Contact name cannot be empty.")

def render_contacts_list_view():
    st.markdown("### 🎙️ The Third Voice - Your Contacts")
    
    if not st.session_state.contacts:
        st.info("No contacts yet. Add your first contact to get started!")
        if st.button("➕ Add New Contact", use_container_width=True):
            st.session_state.app_mode = "add_contact_view"
            st.rerun()
        return
    
    # Sort contacts by most recent activity
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
            f"**{name}** | {time_str}\n_{preview}_",
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

def render_add_contact_view():
    st.markdown("### ➕ Add New Contact")
    
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        st.session_state.app_mode = "contacts_list"
        st.session_state.last_error_message = None
        st.rerun()
    
    with st.form("add_contact_form"):
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="add_contact_name_input_widget")
        context = st.selectbox(
            "Relationship", 
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
            key="add_contact_context_select_widget"
        )
        
        if st.form_submit_button("Add Contact"):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.contacts = load_contacts_and_history()
                    st.success(f"Added {name.strip()}")
                    st.session_state.app_mode = "contacts_list"
                    st.rerun()
            else:
                st.error("Contact name cannot be empty.")

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
        st.rerun()
    
    with st.form("edit_contact_form"):
        name_input = st.text_input("Name", value=contact["name"], key="edit_contact_name_input_widget")
        
        context_options = list(CONTEXTS.keys())
        initial_context_index = context_options.index(contact["context"]) if contact["context"] in context_options else 0
        context = st.selectbox(
            "Relationship", 
            context_options,
            index=initial_context_index,
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
            key="edit_contact_context_select"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                new_name = name_input.strip()
                if not new_name:
                    st.error("Contact name cannot be empty.")
                elif save_contact(new_name, context, contact["id"]):
                    if st.session_state.active_contact == contact["name"]:
                        st.session_state.active_contact = new_name
                    st.success(f"Updated {new_name}")
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.app_mode = "conversation_view"
                    st.session_state.edit_contact = None
                    st.rerun()
        
        with col2:
            if st.form_submit_button("🗑️ Delete Contact"):
                if delete_contact(contact["id"]):
                    st.success(f"Deleted contact: {contact['name']}")
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.app_mode = "contacts_list"
                    st.session_state.active_contact = None
                    st.session_state.edit_contact = None
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
    
    # Navigation buttons
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
            st.session_state.app_mode = "edit_contact_view"
            st.rerun()
    
    st.markdown("---")
    
    # Input section
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
    
    # Action buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Transform", key="transform_message", use_container_width=True):
            input_message = st.session_state.conversation_input_text
            process_message(contact_name, input_message, context)
    
    with col2:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    
    # Error display
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    
    st.markdown("---")
    
    # AI Response section
    st.markdown("#### 🤖 AI Response")
    last_response_key = f"last_response_{contact_name}"
    
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        
        # Show response if it's recent (within 5 minutes)
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
            # Clear old response
            del st.session_state[last_response_key]
            st.info("💭 Your AI response will appear here after you click Transform")
    else:
        st.info("💭 Your AI response will appear here after you click Transform")
    
    st.markdown("---")
    
    # Conversation History
    st.markdown("#### 📜 Conversation History")
    
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total)")
        
        with st.expander("View Chat History", expanded=False):
            # Show most recent messages first
            for msg in reversed(history[-10:]):
                st.markdown(f"""
                **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                """)
                
                with st.container():
                    st.markdown("**Your Message:**")
                    st.info(msg['original'])
                
                if msg['result']:  # Only show AI guidance if it exists
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

# --- Main Application Flow ---
def main():
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    def restore_session():
        """Restore user session on app reload"""
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                if not st.session_state.get("authenticated", False):
                    st.session_state.authenticated = True
                    st.session_state.user = session.user
                    st.session_state.contacts = load_contacts_and_history()
                    
                    if st.session_state.contacts:
                        st.session_state.app_mode = "contacts_list"
                    else:
                        st.session_state.app_mode = "first_time_setup"
        except Exception as e:
            st.warning(f"Could not restore session: {e}")
    
    restore_session()
    
    # Sidebar
    with st.sidebar:
        st.image("https://placehold.co/150x50/ADD8E6/000?text=The+Third+Voice+AI", use_container_width=True)
        st.title("The Third Voice AI")
        
        if st.session_state.authenticated:
            st.write(f"Logged in as: **{st.session_state.user.email}**")
            st.write(f"User ID: `{st.session_state.user.id[:8]}...`")
            
            if st.button("Logout", use_container_width=True):
                sign_out()
        
        st.markdown("---")
        st.subheader("🚀 Debug Info")
        
        if st.checkbox("Show Debug Details"):
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None
                
                debug_info = {
                    "Connection Status": "Connected" if session else "Not Connected",
                    "User ID": user.id[:8] + "..." if user else None,
                    "User Email": user.email if user else None,
                    "Contacts Loaded": len(st.session_state.contacts),
                    "Active Contact": st.session_state.active_contact,
                    "App Mode": st.session_state.app_mode,
                    "Secrets Status": {
                        "Supabase URL": bool(st.secrets.get("supabase", {}).get("url")),
                        "Supabase Key": bool(st.secrets.get("supabase", {}).get("key")),
                        "OpenRouter API Key": bool(st.secrets.get("openrouter", {}).get("api_key")),
                    }
                }
                
                # Test database connection
                try:
                    test_query = supabase.table("contacts").select("id").limit(1).execute()
                    debug_info["Database Test"] = f"OK - {len(test_query.data)} contacts visible"
                except Exception as e:
                    debug_info["Database Test"] = f"Error: {e}"
                
                st.code(json.dumps(debug_info, indent=2, default=str), language="json")
                
            except Exception as e:
                st.error(f"Error generating debug info: {e}")
    
    # Main content routing
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
