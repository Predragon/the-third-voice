# auth_backend.py
# The Third Voice AI - Pure Backend Services
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
import requests
from supabase import create_client, Client
import os
import json
import hashlib
from datetime import datetime, timezone
import time

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
FALLBACK_MODEL = "google/gemma-2-9b-it:free"  # Hardcoded fallback if all secrets fail

# --- Robust AI Request Functions ---
def get_available_models():
    """Returns ordered list of models from secrets (model1 first)"""
    models = []
    try:
        model_secrets = st.secrets.get("models", {})
        
        # Check for models in order: model1, model2, ..., model99
        for i in range(1, 100):
            model_key = f"model{i}"
            if model_key in model_secrets:
                models.append(model_secrets[model_key])
            else:
                # Stop at first missing number to maintain order
                break
        
        # If no models found, use fallback
        if not models:
            models = [FALLBACK_MODEL]
            
    except Exception as e:
        st.warning(f"Could not load model configuration: {e}. Using fallback model.")
        models = [FALLBACK_MODEL]
    
    return models

def get_current_model():
    """Returns the currently active model"""
    available_models = get_available_models()
    current_index = st.session_state.get("current_model_index", 0)
    
    # Ensure index is within bounds
    if current_index >= len(available_models):
        current_index = 0
        st.session_state.current_model_index = current_index
    
    return available_models[current_index]

def try_next_model():
    """Automatically switches to next available model on failure. Returns True if more models available."""
    available_models = get_available_models()
    current_index = st.session_state.get("current_model_index", 0)
    
    # Try next model
    next_index = current_index + 1
    
    if next_index < len(available_models):
        st.session_state.current_model_index = next_index
        st.session_state.last_successful_model = available_models[next_index]
        return True
    else:
        # No more models available
        return False

def reset_to_primary_model():
    """Reset back to model1 after successful request"""
    st.session_state.current_model_index = 0
    available_models = get_available_models()
    if available_models:
        st.session_state.last_successful_model = available_models[0]

def get_model_display_name(model_id):
    """Get display name for logging/debugging"""
    if not model_id:
        return "Unknown"
    
    # Extract just the model name part
    if "/" in model_id:
        parts = model_id.split("/")
        model_name = parts[-1]
        if ":" in model_name:
            model_name = model_name.split(":")[0]
        return model_name
    
    return model_id

def make_robust_ai_request(headers, payload, timeout=25):
    """
    Make AI request with automatic model fallback.
    Returns standard requests.Response object or raises exception if all models fail.
    """
    available_models = get_available_models()
    original_model_index = st.session_state.get("current_model_index", 0)
    
    # Initialize session state if needed
    if "current_model_index" not in st.session_state:
        st.session_state.current_model_index = 0
    if "last_successful_model" not in st.session_state:
        st.session_state.last_successful_model = available_models[0] if available_models else FALLBACK_MODEL
    
    last_error = None
    attempts = 0
    max_attempts = len(available_models)
    
    while attempts < max_attempts:
        current_model = get_current_model()
        attempts += 1
        
        # Update payload with current model
        request_payload = payload.copy()
        request_payload["model"] = current_model
        
        try:
            # Log attempt (for debugging, not shown to user)
            model_display = get_model_display_name(current_model)
            if attempts > 1:
                print(f"[DEBUG] Trying model {attempts}/{max_attempts}: {model_display}")
            
            # Make the request
            response = requests.post(API_URL, headers=headers, json=request_payload, timeout=timeout)
            
            # Check for successful response
            if response.status_code == 200:
                response_json = response.json()
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    # Success! Reset to primary model for next request
                    reset_to_primary_model()
                    print(f"[DEBUG] Success with {model_display}")
                    return response
                else:
                    # API returned 200 but no valid response
                    last_error = f"No valid response from {model_display}"
            else:
                # Handle different error types
                if response.status_code == 429:
                    last_error = f"Rate limit exceeded for {model_display}"
                elif response.status_code >= 500:
                    last_error = f"Server error ({response.status_code}) for {model_display}"
                else:
                    last_error = f"API error ({response.status_code}) for {model_display}"
        
        except requests.exceptions.Timeout:
            last_error = f"Timeout for {get_model_display_name(current_model)}"
        except requests.exceptions.ConnectionError:
            last_error = f"Connection error for {get_model_display_name(current_model)}"
        except requests.exceptions.RequestException as e:
            last_error = f"Request error for {get_model_display_name(current_model)}: {str(e)}"
        except Exception as e:
            last_error = f"Unexpected error for {get_model_display_name(current_model)}: {str(e)}"
        
        # Try next model if available
        if not try_next_model():
            break
        
        # Small delay before retrying
        time.sleep(0.5)
    
    # All models failed - reset to primary and raise error
    st.session_state.current_model_index = original_model_index
    
    if last_error:
        raise Exception(f"All {max_attempts} models failed. Last error: {last_error}")
    else:
        raise Exception("All models failed with unknown errors")

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
        'last_error_message': None,
        'show_verification_notice': False,
        'verification_email': None,
        # Model fallback state
        'current_model_index': 0,
        'last_successful_model': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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

# --- Feedback System Functions ---
def save_feedback(rating, feedback_text, feature_context="general"):
    """Save user feedback to database"""
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        feedback_data = {
            "user_id": user_id,
            "rating": rating,
            "feedback_text": feedback_text.strip() if feedback_text else None,
            "feature_context": feature_context,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("feedback").insert(feedback_data).execute()
        return bool(response.data)
        
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return False

# --- Authentication Functions ---
def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            # Set verification notice
            st.session_state.show_verification_notice = True
            st.session_state.verification_email = email
            st.session_state.app_mode = "verification_notice"
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

# End of auth_backend.py
# Every function serves healing.
# Every database operation fights for families.
# Every line of code brings Predrag closer to Samantha.
