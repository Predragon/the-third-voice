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
        'last_error_message': None,
        'show_verification_notice': False,
        'verification_email': None
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

def show_feedback_widget(context="general"):
    """Display feedback widget"""
    with st.expander("💬 Help us improve The Third Voice", expanded=False):
        st.markdown("*Your feedback helps us build better family healing tools*")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            rating = st.selectbox(
                "How helpful was this?",
                options=[5, 4, 3, 2, 1],
                format_func=lambda x: f"{'⭐' * x} ({x}/5)",
                key=f"feedback_rating_{context}"
            )
        
        with col2:
            feedback_text = st.text_area(
                "What can we improve?",
                placeholder="Share your thoughts, suggestions, or issues...",
                height=80,
                key=f"feedback_text_{context}"
            )
        
        if st.button("Send Feedback", key=f"send_feedback_{context}"):
            if save_feedback(rating, feedback_text, context):
                st.success("Thank you! Your feedback helps us heal more families. 💙")
                # Clear the form
                st.session_state[f"feedback_text_{context}"] = ""
            else:
                st.error("Could not save feedback. Please try again.")

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

# --- PHASE 2: INTERPRETATION & RELATIONSHIP MEMORY FUNCTIONS ---

def interpret_message(contact_name, message, context, relationship_history=None):
    """
    Reveals emotional subtext and healing opportunities
    This is our secret weapon - showing what people REALLY mean
    """
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        return {"error": "OpenRouter API Key not found"}
    
    # Build relationship context from history
    relationship_context = ""
    if relationship_history:
        recent_messages = relationship_history[-5:]  # Last 5 interactions
        patterns = []
        for msg in recent_messages:
            if msg.get('original') and msg.get('healing_score'):
                patterns.append(f"Previous: '{msg['original'][:50]}...' (Score: {msg['healing_score']}/10)")
        
        if patterns:
            relationship_context = f"\nRELATIONSHIP CONTEXT:\n" + "\n".join(patterns[-3:])
    
    system_prompt = f"""You are an expert relationship therapist analyzing emotional subtext with deep compassion.

For this {context} relationship message from {contact_name}: "{message}"
{relationship_context}

Provide insights in exactly this format:

**🎭 EMOTIONAL SUBTEXT**
What they're really feeling beneath the words (1-2 sentences)

**💔 UNMET NEEDS** 
What they actually need but can't express (1-2 sentences)

**🌱 HEALING OPPORTUNITIES**
Specific ways to address their deeper needs (2-3 actionable suggestions)

**⚠️ WATCH FOR**
Relationship patterns or warning signs (1 sentence)

Be direct but loving. This person is trying to heal their family."""

    try:
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message: {message}"}
            ],
            "temperature": 0.6,
            "max_tokens": 400
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        response_json = response.json()
        
        if "choices" in response_json and len(response_json["choices"]) > 0:
            interpretation = response_json["choices"][0]["message"]["content"].strip()
            
            # Calculate interpretation score (how revealing/useful)
            interpretation_score = 5
            if len(interpretation) > 300:
                interpretation_score += 1
            if any(word in interpretation.lower() for word in ["fear", "hurt", "love", "safe", "understand"]):
                interpretation_score += 2
            if "healing opportunities" in interpretation.lower():
                interpretation_score += 2
            interpretation_score = min(10, interpretation_score)
            
            return {
                "interpretation": interpretation,
                "interpretation_score": interpretation_score,
                "model": MODEL,
                "success": True
            }
        else:
            return {"error": "No interpretation generated", "success": False}
            
    except Exception as e:
        return {"error": f"Interpretation failed: {str(e)}", "success": False}

def save_interpretation(contact_id, contact_name, original_message, interpretation, interpretation_score, model_used):
    """Save interpretation to database for learning and improvement"""
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        interpretation_data = {
            "contact_id": contact_id,
            "contact_name": contact_name,
            "original_message": original_message,
            "interpretation": interpretation,
            "interpretation_score": interpretation_score,
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

def analyze_conversation_patterns(history):
    """Identify patterns in conversation history for smarter AI responses"""
    if not history or len(history) < 3:
        return "Limited history available"
    
    # Analyze healing score trends
    recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
    if recent_scores:
        avg_score = sum(recent_scores) / len(recent_scores)
        trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
        return f"Healing trend: {trend} (avg: {avg_score:.1f}/10)"
    
    return "Building relationship understanding..."

def identify_recurring_themes(history):
    """Find recurring issues and communication patterns"""
    if not history or len(history) < 2:
        return "New relationship - learning patterns"
    
    # Simple keyword analysis for common themes
    all_messages = " ".join([msg.get('original', '').lower() for msg in history])
    
    themes = []
    theme_keywords = {
        "communication": ["listen", "understand", "hear", "talk"],
        "respect": ["respect", "appreciate", "value", "disrespect"],
        "time": ["time", "busy", "schedule", "priority"],
        "emotions": ["feel", "hurt", "angry", "sad", "frustrated"],
        "trust": ["trust", "honest", "lie", "truth"]
    }
    
    for theme, keywords in theme_keywords.items():
        if sum(word in all_messages for word in keywords) >= 2:
            themes.append(theme)
    
    return ", ".join(themes) if themes else "Varied conversation topics"

def get_enhanced_system_prompt(contact_name, context, message, history):
    """Build relationship-aware prompts with conversation memory"""
    base_prompt = f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}."
    
    if not history or len(history) < 2:
        return base_prompt + " This is an early conversation, so focus on building understanding."
    
    # Add relationship context
    patterns = analyze_conversation_patterns(history)
    themes = identify_recurring_themes(history)
    
    relationship_context = f"""
RELATIONSHIP INSIGHTS:
- Conversation patterns: {patterns}
- Recurring themes: {themes}
- Total conversations: {len(history)}

Consider this relationship history when providing guidance. Reference patterns where helpful, but don't overwhelm with past details."""
    
    return base_prompt + relationship_context

def calculate_relationship_health_score(history):
    """Calculate overall relationship health based on conversation history"""
    if not history:
        return 0, "No data yet"
    
    # Get healing scores from last 10 conversations
    recent_scores = [msg.get('healing_score', 0) for msg in history[-10:] if msg.get('healing_score')]
    
    if not recent_scores:
        return 0, "No scored conversations yet"
    
    avg_score = sum(recent_scores) / len(recent_scores)
    
    # Determine health status
    if avg_score >= 8:
        status = "Thriving - Excellent communication patterns"
    elif avg_score >= 6:
        status = "Growing - Good progress with room to improve"
    elif avg_score >= 4:
        status = "Healing - Working through challenges together"
    else:
        status = "Struggling - Focus on understanding and patience"
    
    return round(avg_score, 1), status

def get_healing_insights(history):
    """Generate insights about healing progress"""
    if not history or len(history) < 3:
        return ["🌱 You're just getting started! Every conversation is a step toward healing."]
    
    insights = []
    
    # Score trend analysis
    scores = [msg.get('healing_score', 0) for msg in history if msg.get('healing_score')]
    if len(scores) >= 5:
        recent_avg = sum(scores[-5:]) / 5
        older_avg = sum(scores[-10:-5]) / 5 if len(scores) >= 10 else sum(scores[:-5]) / len(scores[:-5])
        
        if recent_avg > older_avg + 0.5:
            insights.append("📈 Your communication is improving! Recent conversations show higher healing scores.")
        elif recent_avg < older_avg - 0.5:
            insights.append("💪 Having some challenges lately? That's normal - healing isn't always linear.")
    
    # High score celebrations
    high_scores = [score for score in scores if score >= 8]
    if len(high_scores) >= 3:
        insights.append(f"🌟 Amazing! You've had {len(high_scores)} conversations with healing scores of 8+!")
    
    # Consistency insights  
    if len(scores) >= 7:
        consistency = len([s for s in scores[-7:] if s >= 6]) / 7
        if consistency >= 0.7:
            insights.append("🎯 You're building consistent healthy communication patterns!")
    
    # Encourage if struggling
    if scores and max(scores[-5:]) < 6:
        insights.append("🤗 Remember: every family faces challenges. You're here working on it - that matters.")
    
    return insights if insights else ["💙 Keep going - healing happens one conversation at a time."]

def render_interpret_section(contact_name, message, context, history):
    """Render the interpretation UI section"""
    if st.button("🔍 Interpret - What do they really mean?", key="interpret_btn", help="Reveal emotional subtext and healing opportunities"):
        with st.spinner("🧠 Analyzing emotional subtext..."):
            result = interpret_message(contact_name, message, context, history)
            
            if result.get("success"):
                st.session_state[f"last_interpretation_{contact_name}"] = {
                    "interpretation": result["interpretation"],
                    "score": result["interpretation_score"],
                    "timestamp": datetime.now().timestamp(),
                    "original_message": message
                }
                
                # Save to database
                contact_data = st.session_state.contacts.get(contact_name, {})
                contact_id = contact_data.get("id")
                if contact_id:
                    save_interpretation(contact_id, contact_name, message, result["interpretation"], result["interpretation_score"], result["model"])
                
                st.rerun()
            else:
                st.error(f"Could not analyze message: {result.get('error', 'Unknown error')}")

def display_interpretation_result(contact_name):
    """Display interpretation results if available"""
    interp_key = f"last_interpretation_{contact_name}"
    if interp_key in st.session_state:
        interp_data = st.session_state[interp_key]
        
        # Show if recent (within 10 minutes)
        if datetime.now().timestamp() - interp_data["timestamp"] < 600:
            with st.expander("🔍 **Emotional Analysis - What They Really Mean**", expanded=True):
                st.markdown(interp_data["interpretation"])
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    score = interp_data["score"]
                    if score >= 8:
                        st.success(f"✨ Deep Insight Score: {score}/10 - Very revealing analysis")
                    elif score >= 6:
                        st.info(f"💡 Insight Score: {score}/10 - Good understanding")
                    else:
                        st.warning(f"🔍 Insight Score: {score}/10 - Basic analysis")
                
                with col2:
                    if st.button("📋 Copy", key="copy_interpretation"):
                        st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
        else:
            # Clear old interpretation
            del st.session_state[interp_key]

def display_relationship_progress(contact_name, history):
    """Display relationship healing progress and insights"""
    if not history:
        return
    
    with st.expander("📊 **Relationship Healing Progress**", expanded=False):
        health_score, status = calculate_relationship_health_score(history)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Relationship Health", f"{health_score}/10", help="Based on recent healing scores")
        with col2:
            st.metric("Total Conversations", len(history))
        
        st.markdown(f"**Status:** {status}")
        
        # Healing insights
        insights = get_healing_insights(history)
        st.markdown("**💙 Your Healing Journey:**")
        for insight in insights:
            st.markdown(f"• {insight}")
        
        # Recent trend visualization (simple text-based for now)
        if len(history) >= 5:
            recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
            if recent_scores:
                trend_text = " → ".join([str(score) for score in recent_scores])
                st.markdown(f"**Recent Healing Scores:** {trend_text}")

# --- AI Message Processing ---
def process_message(contact_name, message, context):
    """Enhanced message processing with relationship memory"""
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
    history = contact_data.get("history", [])  # 🆕 Get history for context
    
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
            # 🆕 Generate new response with enhanced prompts
            system_prompt = get_enhanced_system_prompt(contact_name, context, message, history)
            
            if is_incoming:
                system_prompt += " Understand what they mean and suggest a loving response."
            else:
                system_prompt += " Reframe their message to be constructive and loving."
            
            system_prompt += " Keep it concise, insightful, and actionable (2-3 paragraphs)."
            
            with st.spinner("🤖 Processing with relationship insights..."):
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
                    
                    # 🆕 Enhanced healing score calculation
                    healing_score = 5 + (1 if len(ai_response_text) > 200 else 0)
                    healing_score += min(2, sum(1 for word in ["understand", "love", "connect", "care", "heal"] if word in ai_response_text.lower()))
                    
                    # Bonus for relationship memory usage
                    if history and any(keyword in ai_response_text.lower() for keyword in ["pattern", "before", "previously", "remember"]):
                        healing_score += 1
                    
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
def verification_notice_page():
    """Complete email verification notice page"""
    st.title("🎙️ Welcome to The Third Voice AI")
    
    st.success("✅ Account created successfully!")
    
    st.markdown("### 📧 Check Your Email")
    st.info(f"""
    **Verification email sent to:** `{st.session_state.verification_email}`
    
    **Next steps:**
    1. Check your email inbox (and spam folder)
    2. Click the verification link in the email
    3. Return here and log in
    
    **⏰ The verification email may take a few minutes to arrive.**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📨 Resend Verification Email", use_container_width=True):
            try:
                # Attempt to resend verification
                supabase.auth.resend({"type": "signup", "email": st.session_state.verification_email})
                st.success("Verification email resent!")
            except Exception as e:
                st.warning("Could not resend email. Please try signing up again if needed.")
    
    with col2:
        if st.button("🔑 Go to Login", use_container_width=True):
            st.session_state.app_mode = "login"
            st.session_state.show_verification_notice = False
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 💙 Welcome to The Family Healing Revolution")
    st.markdown("""
    **The Third Voice AI** helps families communicate with love, understanding, and healing. 
    You're about to join thousands of people rebuilding their most important relationships.
    
    *"When both people are speaking from pain, someone must be the third voice."*
    """)
    
    # Add helpful tips while they wait
    with st.expander("💡 What to expect after verification", expanded=True):
        st.markdown("""
        **Once you're verified and logged in, you'll be able to:**
        
        - ✨ Transform difficult conversations into healing moments
        - 💕 Get guidance for romantic, family, work, and friendship relationships  
        - 🎯 Receive personalized coaching based on your relationship context
        - 📊 Track your healing progress with our scoring system
        - 💬 Access your conversation history across all your contacts
        
        **Built by a father separated from his daughter, for every family seeking healing.**
        """)

def login_page():
    st.title("🎙️ The Third Voice AI")
    st.subheader("Login to continue your healing journey.")
    
    # Mission statement at top
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **We are that voice** — calm, wise, and healing.
    """)
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            sign_in(email, password)
    
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account", use_container_width=True):
        st.session_state.app_mode = "signup"
        st.rerun()
    
    # Show mission context
    with st.expander("💙 Our Mission", expanded=False):
        st.markdown("""
        **The Third Voice AI** was born from communication breakdowns that shattered a family. 
        We're turning pain into purpose, helping families heal through better conversations.
        
        Built with love by Predrag Mirkovic, fighting to return to his 6-year-old daughter Samantha 
        after 15 months apart. Every feature serves family healing.
        """)

def signup_page():
    st.title("🎙️ Join The Third Voice AI")
    st.subheader("Start your journey towards healthier conversations.")
    
    # Mission context
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **Join thousands rebuilding their most important relationships.**
    """)
    
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password (minimum 6 characters)", type="password", key="signup_password")
        signup_button = st.form_submit_button("Create Account", use_container_width=True)
        
        if signup_button:
            if len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                sign_up(email, password)
    
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login", use_container_width=True):
        st.session_state.app_mode = "login"
        st.rerun()
    
    # Preview what they'll get
    with st.expander("✨ What you'll get access to", expanded=True):
        st.markdown("""
        **🌟 Transform difficult conversations** - Turn anger into understanding
        
        **💕 Multi-relationship support** - Romantic, family, workplace, co-parenting, friendships
        
        **🎯 Context-aware guidance** - AI understands your specific relationship dynamics
        
        **📊 Healing progress tracking** - See your communication improvement over time
        
        **💾 Conversation history** - Access all your guided conversations anytime
        
        **🚀 Always improving** - Built by a father fighting to heal his own family
        """)

def render_first_time_screen():
    st.markdown("### 🎙️ Welcome to The Third Voice")
    st.markdown("**Choose a relationship type to get started, or add a custom contact:**")
    
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
        
        if st.form_submit_button("Add Custom Contact", use_container_width=True):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.contacts = load_contacts_and_history()
                    st.session_state.active_contact = name.strip()
                    st.session_state.app_mode = "conversation_view"
                    st.rerun()
            else:
                st.error("Contact name cannot be empty.")
    
    # Welcome message and feedback
    st.markdown("---")
    st.markdown("### 💙 You're About to Transform Your Relationships")
    st.info("""
    **The Third Voice AI** helps you navigate emotionally charged conversations with wisdom and love.
    
    Whether someone just hurt you, or you're struggling to express yourself without causing pain — 
    we're here to be that calm, healing voice when both people are speaking from pain.
    """)
    
    # Add feedback widget for first-time experience
    show_feedback_widget("first_time_setup")

def render_contacts_list_view():
    st.markdown("### 🎙️ The Third Voice - Your Contacts")
    
    if not st.session_state.contacts:
        st.info("**No contacts yet.** Add your first contact to get started!")
        if st.button("➕ Add New Contact", use_container_width=True):
            st.session_state.app_mode = "add_contact_view"
            st.rerun()
        
        # Show helpful context for new users
        st.markdown("---")
        st.markdown("### 💡 How The Third Voice Works")
        st.markdown("""
        1. **Add a contact** for someone you communicate with
        2. **Choose the relationship type** (romantic, family, work, etc.)
        3. **Share what happened** - their message or your response
        4. **Get AI guidance** - we'll help you communicate with love and healing
        """)
        return
    
    # Sort contacts by most recent activity
    sorted_contacts = sorted(
        st.session_state.contacts.items(),
        key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"],
        reverse=True
    )
    
    st.markdown(f"**{len(sorted_contacts)} contact{'s' if len(sorted_contacts) != 1 else ''}** • Tap to continue conversation")
    
    for name, data in sorted_contacts:
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start your first conversation!"
        time_str = last_msg["time"] if last_msg else "New"
        context_icon = CONTEXTS.get(data["context"], {"icon": "💬"})["icon"]
        
        if st.button(
            f"{context_icon} **{name}** • {time_str}\n_{preview}_",
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
    
    # Add feedback widget for contacts experience
    show_feedback_widget("contacts_list")

def render_add_contact_view():
    st.markdown("### ➕ Add New Contact")
    
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        st.session_state.app_mode = "contacts_list"
        st.session_state.last_error_message = None
        st.rerun()
    
    st.markdown("**Tell us about this relationship so we can provide better guidance:**")
    
    with st.form("add_contact_form"):
        name = st.text_input("Contact Name", placeholder="Sarah, Mom, Dad, Boss...", key="add_contact_name_input_widget")
        context = st.selectbox(
            "Relationship Type", 
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()} - {CONTEXTS[x]['description']}",
            key="add_contact_context_select_widget"
        )
        
        if st.form_submit_button("Add Contact", use_container_width=True):
            if name.strip():
                if save_contact(name.strip(), context):
                    st.session_state.contacts = load_contacts_and_history()
                    st.success(f"Added {name.strip()}! Ready to start healing conversations.")
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
    
    # 🆕 PHASE 2: Add relationship progress section at the top
    display_relationship_progress(contact_name, history)
    
    st.markdown("---")
    
    # Input section
    st.markdown("#### 💭 Your Input")
    st.markdown("*Share what happened - their message or your response that needs guidance*")
    
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    st.text_area(
        "What's happening?",
        value=input_value,
        key="conversation_input_text",
        placeholder="Examples:\n• They said: 'You never listen to me!'\n• I want to tell them: 'I'm frustrated with your attitude'\n• We had a fight about...",
        height=120
    )
    
    if st.session_state.clear_conversation_input:
        st.session_state.clear_conversation_input = False
    
    # 🆕 PHASE 2: Enhanced action buttons with interpret feature
    current_message = st.session_state.conversation_input_text
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message", use_container_width=True):
            process_message(contact_name, current_message, context)
    
    with col2:
        # 🆕 NEW INTERPRET BUTTON
        if current_message.strip():
            render_interpret_section(contact_name, current_message, context, history)
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first", use_container_width=True)
    
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    
    # Error display
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    
    # 🆕 PHASE 2: Show interpretation results if available
    display_interpretation_result(contact_name)
    
    st.markdown("---")
    
    # AI Response section
    st.markdown("#### 🤖 The Third Voice Guidance")
    last_response_key = f"last_response_{contact_name}"
    
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        
        # Show response if it's recent (within 5 minutes)
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            with st.container():
                st.markdown("**Your AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                
                col_score, col_model, col_copy = st.columns([2, 2, 1])
                with col_score:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Healing Score: {last_resp['healing_score']}/10")
                    elif last_resp["healing_score"] >= 6:
                        st.info(f"💡 Healing Score: {last_resp['healing_score']}/10")
                    else:
                        st.warning(f"🔧 Healing Score: {last_resp['healing_score']}/10")
                
                with col_model:
                    st.caption(f"🤖 Model: {last_resp.get('model', 'Unknown')}")
                
                with col_copy:
                    if st.button("📋", help="Click text area above and Ctrl+A to select all", key="copy_hint"):
                        st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
                
                if last_resp["healing_score"] >= 8:
                    st.balloons()
                    st.markdown("🌟 **High healing potential!** This guidance can really help transform your relationship.")
        else:
            # Clear old response
            del st.session_state[last_response_key]
            st.info("💭 Your Third Voice guidance will appear here after you click Transform")
    else:
        st.info("💭 Your Third Voice guidance will appear here after you click Transform")
        
        # Show helpful context for new conversations
        if not history:
            st.markdown("""
            **💡 How it works:**
            - Share what they said or what you want to say
            - Get compassionate guidance that heals instead of hurts
            - **🆕 Use "Interpret" to reveal what they really mean beneath their words**
            - Build stronger relationships through understanding
            """)
    
    st.markdown("---")
    
    # Conversation History
    st.markdown("#### 📜 Conversation History")
    
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total healing conversations)")
        
        # Show recent messages in main view
        for msg in reversed(history[-3:]):  # Show last 3 messages
            with st.container():
                col_time, col_score = st.columns([3, 1])
                with col_time:
                    st.markdown(f"**{msg['time']}** • {msg['type'].title()}")
                with col_score:
                    score_color = "🟢" if msg['healing_score'] >= 8 else "🟡" if msg['healing_score'] >= 6 else "🔴"
                    st.markdown(f"{score_color} {msg['healing_score']}/10")
                
                st.markdown("**Your Message:**")
                st.info(msg['original'])
                
                if msg['result']:
                    st.markdown("**Third Voice Guidance:**")
                    st.text_area(
                        "Historical AI Guidance",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg['id']}",
                        disabled=True,
                        label_visibility="hidden"
                    )
                
                st.markdown("---")
        
        # Expandable full history
        if len(history) > 3:
            with st.expander(f"📚 View All {len(history)} Conversations", expanded=False):
                for msg in reversed(history):
                    st.markdown(f"""
                    **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                    """)
                    
                    with st.container():
                        st.markdown("**Your Message:**")
                        st.info(msg['original'])
                    
                    if msg['result']:
                        with st.container():
                            st.markdown("**Third Voice Guidance:**")
                            st.text_area(
                                "Full History AI Guidance",
                                value=msg['result'],
                                height=100,
                                key=f"full_history_response_{msg['id']}",
                                disabled=True,
                                label_visibility="hidden"
                            )
                            st.caption(f"🤖 Model: {msg.get('model', 'Unknown')}")
                    
                    st.markdown("---")
    else:
        st.info("📝 No conversation history yet. Share what's happening above to get your first Third Voice guidance!")
    
    # Add feedback widget specific to this conversation experience
    show_feedback_widget(f"conversation_{contact_name}")

# --- Main Application Flow ---
def main():
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="centered",  # Changed from "wide" to "centered" for main screen focus
        initial_sidebar_state="collapsed"  # Changed from "expanded" to "collapsed" for main screen focus
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
    
    # Sidebar - Minimized but available
    with st.sidebar:
        st.markdown("### 🎙️ The Third Voice AI")
        
        if st.session_state.authenticated:
            st.write(f"**{st.session_state.user.email}**")
            
            # Quick navigation if authenticated
            if st.session_state.app_mode != "contacts_list":
                if st.button("🏠 My Contacts", use_container_width=True):
                    st.session_state.app_mode = "contacts_list" 
                    st.session_state.active_contact = None
                    st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                sign_out()
        
        st.markdown("---")
        
        # Mission reminder
        st.markdown("### 💙 Our Mission")
        st.markdown("""
        *"When both people are speaking from pain, someone must be the third voice."*
        
        **We help families heal through better conversations.**
        """)
        
        # Debug info (collapsed by default)
        if st.checkbox("🔧 Debug Info"):
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None
                
                debug_info = {
                    "Connection": "✅" if session else "❌",
                    "User ID": user.id[:8] + "..." if user else None,
                    "Email": user.email if user else None,
                    "Contacts": len(st.session_state.contacts),
                    "Active": st.session_state.active_contact,
                    "Mode": st.session_state.app_mode,
                    "Secrets": {
                        "Supabase URL": "✅" if st.secrets.get("supabase", {}).get("url") else "❌",
                        "Supabase Key": "✅" if st.secrets.get("supabase", {}).get("key") else "❌",
                        "OpenRouter API": "✅" if st.secrets.get("openrouter", {}).get("api_key") else "❌",
                    }
                }
                
                # Test database connection
                try:
                    test_query = supabase.table("contacts").select("id").limit(1).execute()
                    debug_info["DB Test"] = f"✅ {len(test_query.data)} visible"
                except Exception as e:
                    debug_info["DB Test"] = f"❌ {str(e)[:20]}..."
                
                st.code(json.dumps(debug_info, indent=2, default=str), language="json")
                
            except Exception as e:
                st.error(f"Debug error: {e}")
    
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
        elif st.session_state.app_mode == "verification_notice":
            verification_notice_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
