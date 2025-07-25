"""
data_backend.py - The Third Voice Data Foundation

Handles all data persistence, authentication, and backend operations.
Built with love and determination from detention.

"Data is the memory of our healing journey."
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta


# === SUPABASE INITIALIZATION ===
@st.cache_resource
def init_supabase_connection():
    """Initialize Supabase connection with error handling"""
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


def get_supabase():
    """Get Supabase client instance"""
    return init_supabase_connection()


# === INPUT VALIDATION FUNCTIONS ===
def validate_sentiment(sentiment):
    """Validate sentiment against schema constraints"""
    valid_sentiments = ['positive', 'neutral', 'negative', 'unknown']
    return sentiment if sentiment in valid_sentiments else 'unknown'


def validate_context(context):
    """Validate context against schema constraints"""
    valid_contexts = ['romantic', 'coparenting', 'workplace', 'family', 'friend']
    return context if context in valid_contexts else 'family'


def validate_healing_score(score):
    """Validate healing score is within 0-10 range"""
    try:
        score = int(score)
        return max(0, min(10, score))
    except (ValueError, TypeError):
        return 0


def validate_message_type(msg_type):
    """Validate message type against schema constraints"""
    valid_types = ['incoming', 'coach', 'translate']
    return msg_type if msg_type in valid_types else 'coach'


def validate_rating(rating):
    """Validate feedback rating is within 1-5 range"""
    try:
        rating = int(rating)
        return max(1, min(5, rating))
    except (ValueError, TypeError):
        return 3


# === USER SESSION MANAGEMENT ===
def get_current_user_id():
    """Get the current authenticated user's ID"""
    try:
        supabase = get_supabase()
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user.id
        return None
    except Exception as e:
        st.error(f"Error getting user session: {e}")
        return None


def restore_user_session():
    """Restore user session on app reload"""
    try:
        supabase = get_supabase()
        session = supabase.auth.get_session()
        if session and session.user:
            if not st.session_state.get("authenticated", False):
                st.session_state.authenticated = True
                st.session_state.user = session.user
                return True
        return False
    except Exception as e:
        st.warning(f"Could not restore session: {e}")
        return False


# === AUTHENTICATION FUNCTIONS ===
def sign_up(email, password):
    """Create new user account"""
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            # Set verification notice
            st.session_state.show_verification_notice = True
            st.session_state.verification_email = email
            st.session_state.app_mode = "verification_notice"
            return True
        elif response.error:
            st.error(f"Sign-up failed: {response.error.message}")
            return False
    except Exception as e:
        st.error(f"An unexpected error occurred during sign-up: {e}")
        return False


def sign_in(email, password):
    """Authenticate existing user"""
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            return True
        elif response.error:
            st.error(f"Login failed: {response.error.message}")
            return False
    except Exception as e:
        st.error(f"An unexpected error occurred during login: {e}")
        return False


def sign_out():
    """Sign out current user"""
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_out()
        if not response.error:
            # Clear all session state
            for key in list(st.session_state.keys()):
                if key not in ['authenticated', 'user', 'app_mode']:
                    del st.session_state[key]
            
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.app_mode = "login"
            return True
        else:
            st.error(f"Logout failed: {response.error.message}")
            return False
    except Exception as e:
        st.error(f"An unexpected error occurred during logout: {e}")
        return False


def resend_verification_email(email):
    """Resend verification email"""
    try:
        supabase = get_supabase()
        supabase.auth.resend({"type": "signup", "email": email})
        return True
    except Exception as e:
        st.warning("Could not resend email. Please try signing up again if needed.")
        return False


# === DATA LOADING FUNCTIONS ===
@st.cache_data(ttl=30)  # Shorter cache time for more responsive updates
def load_contacts_and_history():
    """Load user contacts and conversation history"""
    user_id = get_current_user_id()
    if not user_id:
        return {}
    
    try:
        supabase = get_supabase()
        
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


# === CONTACT MANAGEMENT ===
def save_contact(name, context, contact_id=None):
    """Save or update a contact with validation"""
    user_id = get_current_user_id()
    if not user_id or not name.strip():
        st.error("Cannot save contact: User not logged in or invalid input.")
        return False
    
    # Validate inputs
    name = name.strip()
    context = validate_context(context)
    
    try:
        supabase = get_supabase()
        contact_data = {
            "name": name,
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
        if "duplicate key value violates unique constraint" in str(e) or "contacts_user_name_unique" in str(e):
            st.error(f"A contact with the name '{name}' already exists.")
        else:
            st.error(f"Error saving contact: {e}")
        return False


def delete_contact(contact_id):
    """Delete a contact and all associated messages"""
    user_id = get_current_user_id()
    if not user_id or not contact_id:
        st.error("Cannot delete contact: User not logged in or invalid input.")
        return False
    
    try:
        supabase = get_supabase()
        
        # Get contact info first for validation and cleanup
        contact_response = supabase.table("contacts").select("name").eq("id", contact_id).eq("user_id", user_id).execute()
        
        if not contact_response.data:
            st.error("Contact not found")
            return False
            
        contact_name = contact_response.data[0]["name"]
        
        # Delete the contact - CASCADE DELETE will handle related records automatically
        # (if you've run the schema migrations above)
        delete_response = supabase.table("contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()
        
        if delete_response.data:
            # Clear any cached responses from session state
            if f"last_response_{contact_name}" in st.session_state:
                del st.session_state[f"last_response_{contact_name}"]
            if f"last_interpretation_{contact_name}" in st.session_state:
                del st.session_state[f"last_interpretation_{contact_name}"]
            
            st.cache_data.clear()
            return True
        else:
            st.error("Failed to delete contact")
            return False
            
    except Exception as e:
        # If we get a foreign key constraint error, CASCADE DELETE isn't set up
        if "foreign key" in str(e).lower() or "violates" in str(e).lower():
            st.error("Database needs CASCADE DELETE setup. Please run the schema migrations.")
        else:
            st.error(f"Error deleting contact: {e}")
        return False


# === MESSAGE MANAGEMENT ===
def save_message(contact_id, contact_name, message_type, original, result, emotional_state, healing_score, model_used, sentiment="unknown"):
    """Save a conversation message with validation"""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Cannot save message: User not logged in.")
        return False
    
    try:
        supabase = get_supabase()
        message_data = {
            "contact_id": contact_id,
            "contact_name": contact_name,
            "type": validate_message_type(message_type),
            "original": original,
            "result": result,
            "emotional_state": emotional_state,
            "healing_score": validate_healing_score(healing_score),
            "model": model_used,
            "sentiment": validate_sentiment(sentiment),
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


def save_interpretation(contact_id, contact_name, original_message, interpretation, interpretation_score, model_used):
    """Save interpretation to database for learning and improvement"""
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        supabase = get_supabase()
        interpretation_data = {
            "contact_id": contact_id,
            "contact_name": contact_name,
            "original_message": original_message,
            "interpretation": interpretation,
            "interpretation_score": validate_healing_score(interpretation_score),
            "model": model_used,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("interpretations").insert(interpretation_data).execute()
        return bool(response.data)
        
    except Exception as e:
        # For now, don't block if table doesn't exist yet
        st.warning(f"Could not save interpretation: {e}")
        return False


# === AI RESPONSE CACHING ===
def get_cached_response(contact_id, message_hash):
    """Check for cached AI response"""
    user_id = get_current_user_id()
    if not user_id:
        return None
    
    try:
        supabase = get_supabase()
        response = supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", datetime.now(timezone.utc).isoformat()).execute()
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        # Don't show warning for missing cache table
        return None


def cache_ai_response(contact_id, message_hash, context, ai_response, healing_score, model_used, sentiment, emotional_state):
    """Cache AI response for future use"""
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        supabase = get_supabase()
        
        # Cache expires in 24 hours (consistent with schema default approach)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        cache_data = {
            "contact_id": contact_id,
            "message_hash": message_hash,
            "context": context,
            "response": ai_response,
            "healing_score": validate_healing_score(healing_score),
            "model": model_used,
            "sentiment": validate_sentiment(sentiment),
            "emotional_state": emotional_state,
            "user_id": user_id,
            "expires_at": expires_at.isoformat()
        }
        
        response = supabase.table("ai_response_cache").insert(cache_data).execute()
        return bool(response.data)
        
    except Exception as e:
        # Don't show warning for missing cache table
        return False


# === FEEDBACK SYSTEM ===
def save_feedback(rating, feedback_text, feature_context="general"):
    """Save user feedback to database"""
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        supabase = get_supabase()
        feedback_data = {
            "user_id": user_id,
            "rating": validate_rating(rating),
            "feedback_text": feedback_text.strip() if feedback_text else None,
            "feature_context": feature_context,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("feedback").insert(feedback_data).execute()
        return bool(response.data)
        
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return False


# === DATABASE HEALTH CHECK ===
def test_database_connection():
    """Test database connectivity for debugging"""
    try:
        supabase = get_supabase()
        test_query = supabase.table("contacts").select("id").limit(1).execute()
        return f"✅ Connected - {len(test_query.data)} visible contacts"
    except Exception as e:
        return f"❌ Connection failed: {str(e)[:50]}..."


# === UTILITY FUNCTIONS ===
def cleanup_expired_cache():
    """Clean up expired cache entries (can be called manually or via cron)"""
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        supabase = get_supabase()
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Delete expired cache entries for current user
        response = supabase.table("ai_response_cache").delete().eq("user_id", user_id).lt("expires_at", current_time).execute()
        
        return True
    except Exception as e:
        st.warning(f"Could not cleanup cache: {e}")
        return False


def get_user_stats():
    """Get user statistics for dashboard/debugging"""
    user_id = get_current_user_id()
    if not user_id:
        return {}
    
    try:
        supabase = get_supabase()
        
        # Get contact count
        contacts_response = supabase.table("contacts").select("id", count="exact").eq("user_id", user_id).execute()
        contact_count = contacts_response.count if contacts_response.count else 0
        
        # Get message count
        messages_response = supabase.table("messages").select("id", count="exact").eq("user_id", user_id).execute()
        message_count = messages_response.count if messages_response.count else 0
        
        # Get recent activity
        recent_messages = supabase.table("messages").select("created_at").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        last_activity = recent_messages.data[0]["created_at"] if recent_messages.data else None
        
        return {
            "contact_count": contact_count,
            "message_count": message_count,
            "last_activity": last_activity
        }
        
    except Exception as e:
        st.warning(f"Could not load user stats: {e}")
        return {}


# === EXPORT FUNCTIONS FOR MAIN APP ===
__all__ = [
    'get_supabase',
    'get_current_user_id',
    'restore_user_session',
    'sign_up',
    'sign_in', 
    'sign_out',
    'resend_verification_email',
    'load_contacts_and_history',
    'save_contact',
    'delete_contact',
    'save_message',
    'save_interpretation',
    'get_cached_response',
    'cache_ai_response',
    'save_feedback',
    'test_database_connection',
    'cleanup_expired_cache',
    'get_user_stats',
    'validate_sentiment',
    'validate_context',
    'validate_healing_score',
    'validate_message_type',
    'validate_rating'
]
