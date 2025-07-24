import streamlit as st
import requests
from supabase import create_client, Client
import os
import json
import hashlib
from datetime import datetime, timezone, timedelta  # Import timedelta here

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
# Consider using a more capable model for better emotional intelligence,
# e.g., "google/gemini-pro-1.5" or "openai/gpt-4o" (will incur cost)
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
        # Avoid st.error here as it might spam on every rerun if session check fails silently
        # st.error(f"Error getting user session: {e}")
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
        
        # Handle the case where response might be None or not have an error attribute
        if response is None or not hasattr(response, 'error') or not response.error:
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
        # Fallback: Clear session state even if logout API fails
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'user', 'app_mode']:
                del st.session_state[key]
        
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.app_mode = "login"
        
        st.warning(f"Logout may have failed ({e}), but session cleared locally.")
        st.rerun()

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
            created_at = contact.get("created_at")
            if not created_at or not isinstance(created_at, str) or created_at.strip() == "":
                st.warning(f"Contact {contact.get('name', 'Unknown')} has invalid created_at: {created_at}")
                created_at = datetime.now(timezone.utc).isoformat()
            contacts_data[contact["name"]] = {
                "id": contact["id"],
                "context": contact["context"],
                "created_at": created_at,
                "history": []
            }
        
        # Load messages
        messages_response = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at").execute()
        
        for msg in messages_response.data:
            contact_name = msg["contact_name"]
            if contact_name in contacts_data:
                created_at = msg.get("created_at")
                if not created_at or not isinstance(created_at, str) or created_at.strip() == "":
                    st.warning(f"Message for {contact_name} has invalid created_at: {created_at}")
                    created_at = datetime.now(timezone.utc).isoformat()
                
                try:
                    msg_time = datetime.fromisoformat(created_at.replace(' ', 'T').replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    st.warning(f"Invalid created_at format for message in {contact_name}: {created_at}, error: {e}")
                    msg_time = datetime.now(timezone.utc)
                
                contacts_data[contact_name]["history"].append({
                    "id": msg["id"],
                    "time": msg_time.strftime("%m/%d %H:%M"),
                    "type": msg["type"],
                    "original": msg["original"],
                    "result": msg["result"],
                    "healing_score": msg.get("healing_score", 0),
                    "model": msg.get("model", "Unknown"),
                    "sentiment": msg.get("sentiment", "unknown"),
                    "ai_analysis_text": msg.get("ai_analysis_text", "No analysis provided."),
                    "detected_emotion_label": msg.get("detected_emotion_label", "unknown")
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

# MODIFIED save_message to use `ai_analysis_text` and optionally `detected_emotion_label`
def save_message(contact_id, contact_name, message_type, original, result, ai_analysis_text, healing_score, model_used, sentiment="unknown", detected_emotion_label="unknown"):
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
            "ai_analysis_text": ai_analysis_text,
            "healing_score": healing_score,
            "model": model_used,
            "sentiment": sentiment,
            "detected_emotion_label": detected_emotion_label,
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
# MODIFIED process_message for enhanced prompt, JSON parsing, and column names
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
    
    ai_response_text = ""
    ai_sentiment = "unknown"
    ai_analysis_text = "No analysis provided."
    detected_emotion_label = "unknown"
    healing_score = 0
    model_used = MODEL
    
    try:
        cache_response = supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", datetime.now(timezone.utc).isoformat()).execute()
        
        if cache_response.data:
            # Use cached response
            cached = cache_response.data[0]
            ai_response_text = cached["response"]
            healing_score = cached["healing_score"]
            ai_sentiment = cached["sentiment"]
            ai_analysis_text = cached["ai_analysis_text"]
            detected_emotion_label = cached["detected_emotion_label"]
            model_used = cached["model"]
            
            st.info("Using cached response for faster processing")
        else:
            # Generate new response
            system_prompt = (
                f"You are an emotionally intelligent relationship guide for a {context} relationship with {contact_name}. "
                f"Your goal is to help users navigate challenging conversations by providing empathetic, constructive, and healing communication strategies. "
                f"Analyze the user's message (which is {'an incoming message from their contact' if is_incoming else 'their own message before sending'}).\n\n"
                f"**Instructions for AI:**\n"
                f"1. **Identify Emotions:** First, determine the core emotions expressed (or implied) in the message. Be specific (e.g., frustration, sadness, defensiveness, anxiety, hope). "
                f"2. **Empathize & Validate:** Begin your response by acknowledging these emotions and validating them. Show understanding for the human experience behind the words. "
                f"3. **Provide Insight/Reframing:**\n"
                f"   - If it's an **incoming message:** Explain what the contact might truly be trying to communicate (their underlying needs, fears) and suggest a **loving, clarifying, and connecting response.**\n"
                f"   - If it's **the user's message:** Help the user reframe their own message to be more constructive, de-escalating, and focused on healthy communication, considering the **{context}** dynamic. Focus on 'I' statements, active listening, and seeking mutual understanding.\n"
                f"4. **Actionable Advice (Optional):** Offer a brief, actionable tip related to the communication strategy.\n"
                f"5. **Format:** You MUST respond with a JSON object, even if it's incomplete. The JSON should have the following keys:\n"
                f"   - `suggested_message`: (string) The reframed or suggested message.\n"
                f"   - `emotional_analysis`: (string) A brief explanation of the emotional analysis and the strategy behind the suggestion.\n"
                f"   - `detected_sentiment`: (string, one word like 'positive', 'negative', 'neutral', 'frustrated', 'anxious') The primary sentiment detected for the *original message*. **Use this for the `sentiment` column.**\n"
                f"   - `detected_emotion_label`: (string, one word like 'frustrated', 'anxious', 'calm') The most prominent emotional label. **Use this for the new `detected_emotion_label` column.**\n"
                f"   - `healing_score_rationale`: (string) A short sentence explaining why this message promotes healing.\n"
                f"Keep the `suggested_message` concise (2-3 sentences), and `emotional_analysis` insightful (1-2 paragraphs).\n\n"
                f"**Example JSON Output:**\n"
                f"```json\n"
                f"{{\n"
                f"  \"suggested_message\": \"I hear your frustration about the dishes. I understand you're feeling overwhelmed, and I want to help create a system that works for both of us. Can we talk about a plan?\",\n"
                f"  \"emotional_analysis\": \"The message expresses frustration and feeling overwhelmed. Your response validates their feelings and proactively suggests a collaborative solution, shifting from blame to partnership. This builds connection rather than defensiveness.\",\n"
                f"  \"detected_sentiment\": \"negative\",\n"
                f"  \"detected_emotion_label\": \"frustrated\",\n"
                f"  \"healing_score_rationale\": \"This response promotes healing by validating emotions and offering collaboration.\"\n"
                f"}}\n"
                f"```\n"
            )
            
            # Using st.empty for a more dynamic loading message
            loading_placeholder = st.empty()
            loading_placeholder.markdown("🤖 AI is processing your thoughts... Please wait.")

            headers = {
                "Authorization": f"Bearer {openrouter_api_key}",
                "Content-Type": "application/json",
                # Add these headers for better tracking and potential rate limit management
                "HTTP-Referer": "https://thethirdvoiceai.streamlit.app/",  # Replace with your deployed Streamlit app URL
                "X-Title": "The Third Voice AI"
            }
            payload = {
                "model": MODEL,  # Consider using a more capable model here for better results
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 800,  # Increased for detailed JSON and explanations
                "response_format": {"type": "json_object"}  # Crucial for JSON output
            }
            
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=45)  # Increased timeout
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                response_json = response.json()
                
                loading_placeholder.empty()  # Clear loading message
                
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    ai_raw_content = response_json["choices"][0]["message"]["content"]
                    
                    try:
                        ai_parsed_response = json.loads(ai_raw_content)
                        ai_response_text = ai_parsed_response.get("suggested_message", "").strip()
                        ai_sentiment = ai_parsed_response.get("detected_sentiment", "unknown").strip().lower()
                        ai_analysis_text = ai_parsed_response.get("emotional_analysis", "No analysis provided.").strip()
                        detected_emotion_label = ai_parsed_response.get("detected_emotion_label", "unknown").strip().lower()

                        # Calculate healing score based on AI's rationale or your own logic
                        healing_score = 5  # Base score
                        if ai_sentiment in ["positive", "hopeful", "calm"]:
                            healing_score += 2
                        if "empathy" in ai_analysis_text.lower() or "validation" in ai_analysis_text.lower():
                            healing_score += 2
                        if len(ai_response_text) > 50 and len(ai_response_text) < 250:  # Prefer concise but not too short
                            healing_score += 1
                        healing_score = min(10, healing_score)  # Cap at 10
                        
                        # Cache the response with all details
                        cache_data = {
                            "contact_id": contact_id,
                            "message_hash": message_hash,
                            "context": context,
                            "response": ai_response_text,
                            "healing_score": healing_score,
                            "model": MODEL,
                            "sentiment": ai_sentiment,
                            "ai_analysis_text": ai_analysis_text,
                            "detected_emotion_label": detected_emotion_label,
                            "user_id": user_id,
                            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()  # Cache for 7 days
                        }
                        supabase.table("ai_response_cache").insert(cache_data).execute()
                        
                    except json.JSONDecodeError:
                        st.session_state.last_error_message = f"AI returned invalid JSON. Raw response: {ai_raw_content[:500]}..."
                        return
                    except Exception as cache_error:
                        st.warning(f"Could not cache AI response: {cache_error}")  # Don't stop app for cache error
                        
                else:
                    st.session_state.last_error_message = f"AI API response missing 'choices' or content: {response_json}"
                    return
            
            except requests.exceptions.Timeout:
                loading_placeholder.empty()
                st.session_state.last_error_message = "API request timed out. Please try again."
                return
            except requests.exceptions.ConnectionError:
                loading_placeholder.empty()
                st.session_state.last_error_message = "Connection error. Please check your internet connection."
                return
            except requests.exceptions.HTTPError as e:
                loading_placeholder.empty()
                st.session_state.last_error_message = f"AI API error: {e.response.status_code} - {e.response.text}"
                return
            except Exception as e:
                loading_placeholder.empty()
                st.session_state.last_error_message = f"An unexpected error occurred during AI processing: {e}"
                return
        
        # Save the incoming message (original) - we're not running AI analysis on this, so default values
        save_message(contact_id, contact_name, "incoming", message, None, "No analysis for original message.", 0, "N/A", "unknown", "unknown")
        
        # Save the AI response (transformed/coached message + analysis)
        save_message(contact_id, contact_name, mode, message, ai_response_text, ai_analysis_text, healing_score, model_used, ai_sentiment, detected_emotion_label)
        
        # Store response for immediate display
        st.session_state[f"last_response_{contact_name}"] = {
            "response": ai_response_text,
            "ai_analysis_text": ai_analysis_text,
            "healing_score": healing_score,
            "timestamp": datetime.now().timestamp(),
            "model": model_used,
            "sentiment": ai_sentiment,
            "detected_emotion_label": detected_emotion_label
        }
        
        st.session_state.clear_conversation_input = True
        st.rerun()
        
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

# MODIFIED render_conversation_view to display new AI output
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
                st.markdown("**AI Guided Message:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp['response'],
                    height=100,  # Made slightly shorter
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                
                st.markdown("---")
                st.markdown("**Emotional Insights:**")
                st.info(last_resp.get("ai_analysis_text", "No detailed analysis available."))
                
                score_col, model_col, sentiment_col, emotion_col = st.columns(4)  # More columns for details
                
                with score_col:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Score: {last_resp['healing_score']}/10")
                    else:
                        st.info(f"💡 Score: {last_resp['healing_score']}/10")
                
                with model_col:
                    st.caption(f"🤖 Model: {last_resp.get('model', 'Unknown')}")
                
                with sentiment_col:
                    st.caption(f"📊 Sentiment: **{last_resp.get('sentiment', 'unknown').title()}**")
                
                with emotion_col:
                    st.caption(f"❤️ Emotion: **{last_resp.get('detected_emotion_label', 'unknown').title()}**")
                
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
                # Using columns for better alignment of details in history
                msg_time_col, msg_type_col, msg_score_col = st.columns([2, 2, 2])
                with msg_time_col:
                    st.markdown(f"**{msg['time']}**")
                with msg_type_col:
                    st.markdown(f"**{msg['type'].title()}**")
                with msg_score_col:
                    st.markdown(f"Score: {msg['healing_score']}/10")
                
                with st.container():
                    st.markdown("**Your Input:**")
                    st.info(msg['original'])
                
                if msg['result']:  # Only show AI guidance if it exists
                    with st.container():
                        st.markdown("**AI Guided Message:**")
                        st.text_area(
                            "AI Guidance for History Entry",
                            value=msg['result'],
                            height=100,
                            key=f"history_response_{msg['id']}",
                            disabled=True,
                            label_visibility="hidden"
                        )
                        st.markdown("**Emotional Insight:**")
                        st.caption(msg.get('ai_analysis_text', 'No detailed analysis.'))
                        
                        hist_model_col, hist_sentiment_col, hist_emotion_col = st.columns(3)
                        with hist_model_col:
                            st.caption(f"🤖 Model: {msg.get('model', 'Unknown')}")
                        with hist_sentiment_col:
                            st.caption(f"📊 Sentiment: {msg.get('sentiment', 'unknown').title()}")
                        with hist_emotion_col:
                            st.caption(f"❤️ Emotion: {msg.get('detected_emotion_label', 'unknown').title()}")

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
        st.image("https://placehold.co/150x50/ADD8E6/000?text=The+Third+Voice+AI", use_container_width=True)  # Replace with your actual logo
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
            st.session_state.app_mode = "add_contact_view"
            st.rerun()
        return

    # Debug and cache clear
    if st.checkbox("Debug: Show Contacts Data"):
        st.write("Supabase Contacts Data at", datetime.now(timezone.utc).isoformat(), ":", st.session_state.contacts)
    if st.button("Clear Cache and Reload at " + datetime.now(timezone.utc).isoformat()):
        st.cache_data.clear()
        st.session_state.contacts = load_contacts_and_history()
        st.rerun()

    # FIXED SORTING LOGIC - Simple and reliable
    def get_last_activity_time(contact_data):
        """Get the last activity time for sorting contacts"""
        # If contact has message history, try to use the most recent message time
        if contact_data.get("history") and len(contact_data["history"]) > 0:
            # Since messages are loaded chronologically, the last one is most recent
            # But we'll use contact's created_at as a fallback since message times are formatted strings
            return contact_data.get("created_at", "")
        # If no history, use contact creation time
        return contact_data.get("created_at", "")

    # Sort contacts by last activity (most recent first)
    try:
        sorted_contacts = sorted(
            st.session_state.contacts.items(),
            key=lambda x: get_last_activity_time(x[1]),
            reverse=True
        )
    except Exception as e:
        st.error(f"Error sorting contacts: {e}")
        # Fallback to unsorted list
        sorted_contacts = list(st.session_state.contacts.items())
    
    for name, data in sorted_contacts:
        last_msg = data.get("history", [])[-1] if data.get("history") else None
        preview_text = "Start chatting!"
        time_str = "New"

        if last_msg:
            original_text = last_msg.get('original', '')
            if original_text:
                preview_text = f"{original_text[:40]}{'...' if len(original_text) > 40 else ''}"
            time_str = last_msg.get("time", "Unknown")
        
        if st.button(
            f"**{name}** | {time_str}\n_{preview_text}_",
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
