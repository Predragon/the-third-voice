import streamlit as st
import datetime
import requests
from supabase import create_client

# Constants
CONTEXTS = {
    "romantic": {"icon": "💕", "description": "Partner & intimate relationships"},
    "coparenting": {"icon": "👨‍👩‍👧‍👦", "description": "Raising children together"},
    "workplace": {"icon": "🏢", "description": "Professional relationships"},
    "family": {"icon": "🏠", "description": "Extended family connections"},
    "friend": {"icon": "🤝", "description": "Friendships & social bonds"}
}

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-2-9b-it:free"

# Initialize Supabase with auth
@st.cache_resource
def init_supabase():
    try:
        supabase = create_client(st.secrets.supabase.url, st.secrets.supabase.key)
        
        # Initialize auth
        if 'auth' not in st.session_state:
            st.session_state.auth = supabase.auth
            
        return supabase
    except Exception as e:
        st.error(f"Supabase initialization failed: {e}")
        return None

supabase = init_supabase()

# Authentication functions
def handle_login(email, password):
    try:
        response = st.session_state.auth.sign_in_with_password({"email": email, "password": password})
        if not response.user:
            st.error("Login failed. Please check your credentials.")
            return False
        st.session_state.user = response.user
        st.session_state.user_id = response.user.id
        st.rerun()
        return True
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

def handle_signup(email, password):
    try:
        response = st.session_state.auth.sign_up({"email": email, "password": password})
        if not response.user:
            st.error("Signup failed. Please try again.")
            return False
        st.success("Account created! Please check your email for verification.")
        return True
    except Exception as e:
        st.error(f"Signup error: {str(e)}")
        return False

def handle_logout():
    try:
        st.session_state.auth.sign_out()
        st.session_state.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Logout error: {str(e)}")

# Load data with user-specific filtering
@st.cache_data(ttl=60)
def load_contacts_and_history():
    if not supabase or 'user_id' not in st.session_state:
        return {}
    
    try:
        # Get contacts for current user only
        contacts_data = {c["name"]: {
            "context": c["context"],
            "history": [],
            "created_at": c.get("created_at", datetime.datetime.now().isoformat()),
            "id": c.get("id")
        } for c in supabase.table("contacts")
                         .select("*")
                         .eq("user_id", st.session_state.user_id)
                         .execute().data}

        # Get messages for current user only
        messages = supabase.table("messages") \
                         .select("*") \
                         .eq("user_id", st.session_state.user_id) \
                         .order("timestamp") \
                         .execute().data

        for msg in messages:
            contact_name = msg["contact_name"]
            if contact_name not in contacts_data:
                contacts_data[contact_name] = {
                    "context": "family",
                    "history": [],
                    "created_at": datetime.datetime.now().isoformat(),
                    "id": None
                }
            contacts_data[contact_name]["history"].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "healing_score": msg.get("healing_score", 0),
                "model": msg.get("model", "Unknown")
            })
        return contacts_data
    except Exception as e:
        st.warning(f"Could not load data: {e}")
        return {}

# Save data with user_id
def save_contact(name, context, contact_id=None):
    if not supabase or not name.strip() or 'user_id' not in st.session_state:
        return False
    
    try:
        contact_data = {
            "name": name, 
            "context": context,
            "user_id": st.session_state.user_id
        }
        
        if contact_id:
            response = supabase.table("contacts") \
                            .update(contact_data) \
                            .eq("id", contact_id) \
                            .eq("user_id", st.session_state.user_id) \
                            .execute()
        else:
            contact_data["created_at"] = datetime.datetime.now().isoformat()
            response = supabase.table("contacts").insert(contact_data).execute()
            
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving contact: {e}")
        return False

def delete_contact(contact_id):
    if not supabase or not contact_id or 'user_id' not in st.session_state:
        return False
    
    try:
        # Get contact name before deleting (with user_id check)
        contact_name_data = supabase.table("contacts") \
                                 .select("name") \
                                 .eq("id", contact_id) \
                                 .eq("user_id", st.session_state.user_id) \
                                 .execute().data
        
        if contact_name_data:
            contact_name = contact_name_data[0]["name"]
            # Delete associated messages (with user_id check)
            supabase.table("messages") \
                  .delete() \
                  .eq("contact_name", contact_name) \
                  .eq("user_id", st.session_state.user_id) \
                  .execute()
            
            if f"last_response_{contact_name}" in st.session_state:
                del st.session_state[f"last_response_{contact_name}"]

        # Delete contact (with user_id check)
        supabase.table("contacts") \
              .delete() \
              .eq("id", contact_id) \
              .eq("user_id", st.session_state.user_id) \
              .execute()
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error deleting contact: {e}")
        return False

def save_message(contact, message_type, original, result, emotional_state, healing_score, model_used):
    if not supabase or 'user_id' not in st.session_state:
        return False
    
    try:
        supabase.table("messages").insert({
            "contact_name": contact,
            "type": message_type,
            "original": original,
            "result": result,
            "emotional_state": emotional_state,
            "healing_score": healing_score,
            "timestamp": datetime.datetime.now().isoformat(),
            "model": model_used,
            "user_id": st.session_state.user_id
        }).execute()
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving message: {e}")
        return False

# Process message with OpenRouter API
def process_message(contact_name, message, context):
    st.session_state.last_error_message = None

    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty. Please type something to transform."
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
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {st.secrets.openrouter.api_key}",
                    "HTTP-Referer": "https://thethirdvoice.streamlit.app"  # Update with your URL
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=25
            ).json()["choices"][0]["message"]["content"].strip()

        healing_score = 5 + (1 if len(response) > 200 else 0) + min(2, sum(1 for word in ["understand", "love", "connect", "care"] if word in response.lower()))
        healing_score = min(10, healing_score)

        new_message = {
            "id": f"{mode}_{datetime.datetime.now().timestamp()}",
            "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
            "type": mode,
            "original": message,
            "result": response,
            "healing_score": healing_score,
            "model": MODEL
        }

        if contact_name not in st.session_state.contacts:
            st.session_state.contacts[contact_name] = {
                "context": "family",
                "history": [],
                "created_at": datetime.datetime.now().isoformat(),
                "id": None
            }

        st.session_state.contacts[contact_name]["history"].append(new_message)
        save_message(contact_name, mode, message, response, "calm", healing_score, MODEL)
        st.session_state[f"last_response_{contact_name}"] = {
            "response": response,
            "healing_score": healing_score,
            "timestamp": datetime.datetime.now().timestamp(),
            "model": MODEL
        }
        st.session_state.clear_conversation_input = True

    except requests.exceptions.Timeout:
        st.session_state.last_error_message = "API request timed out. Please try again. The AI might be busy."
    except requests.exceptions.ConnectionError:
        st.session_state.last_error_message = "Connection error. Please check your internet connection."
    except requests.exceptions.RequestException as e:
        st.session_state.last_error_message = f"Network or API error: {e}. Please check your API key or connection."
    except (KeyError, IndexError) as e:
        st.session_state.last_error_message = f"Received an unexpected response from the AI API. Error: {e}"
    except Exception as e:
        st.session_state.last_error_message = f"An unexpected error occurred: {e}"

# Authentication UI
def render_auth():
    st.title("The Third Voice AI")
    st.markdown("### Please sign in or create an account")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.form_submit_button("Login"):
                if handle_login(email, password):
                    st.success("Logged in successfully!")
    
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            
            if st.form_submit_button("Create Account"):
                if handle_signup(email, password):
                    st.rerun()

# Initialize session with auth check
def initialize_session():
    defaults = {
        "page": "contacts",
        "active_contact": None,
        "edit_contact": None,
        "conversation_input_text": "",
        "clear_conversation_input": False,
        "edit_contact_name_input": "",
        "add_contact_name_input": "",
        "add_contact_context_select": list(CONTEXTS.keys())[0],
        "last_error_message": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    # Initialize contacts only if logged in
    if 'user_id' in st.session_state and 'contacts' not in st.session_state:
        st.session_state.contacts = load_contacts_and_history()

# UI Components (render_first_time_screen, render_contact_list, etc.)
# ... [Keep all your existing UI components exactly as they were]

def main():
    st.set_page_config(page_title="The Third Voice AI", layout="wide")
    
    if supabase is None:
        st.error("Failed to initialize database connection. Please try again later.")
        return
    
    # Check authentication
    if 'user_id' not in st.session_state:
        render_auth()
        return
    
    initialize_session()
    
    # Add logout button to sidebar
    with st.sidebar:
        st.markdown(f"Logged in as: **{st.session_state.user.email}**")
        if st.button("Logout"):
            handle_logout()
    
    # Rest of your existing UI rendering logic
    if not st.session_state.contacts:
        render_first_time_screen()
    else:
        if st.session_state.page == "contacts":
            render_contact_list()
        elif st.session_state.page == "edit_contact":
            render_edit_contact()
        elif st.session_state.page == "add_contact":
            render_add_contact()
        elif st.session_state.page == "conversation":
            render_conversation()

if __name__ == "__main__":
    main()
