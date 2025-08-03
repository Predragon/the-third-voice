import streamlit as st
import hashlib
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
import time
import uuid
from supabase import create_client, Client

# ==========================================
# CONFIGURATION & CONSTANTS SECTION
# ==========================================

class AppConfig:
    """Centralized configuration management"""
    
    # Supabase Configuration
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # AI Model Configuration
    AI_MODEL = "google/gemma-2-9b-it:free"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    
    # App Configuration
    APP_NAME = "The Third Voice AI"
    APP_TAGLINE = "When both people are speaking from pain, someone must be the third voice"
    
    # Cache Settings
    CACHE_EXPIRY_DAYS = 7
    
    # UI Configuration
    MOBILE_BREAKPOINT = 768

class RelationshipContext(Enum):
    """Relationship context types"""
    ROMANTIC = ("romantic", "💕", "Partner & intimate relationships")
    COPARENTING = ("coparenting", "👨‍👩‍👧‍👦", "Raising children together")
    WORKPLACE = ("workplace", "🏢", "Professional relationships")
    FAMILY = ("family", "🏠", "Extended family connections")
    FRIEND = ("friend", "🤝", "Friendships & social bonds")
    
    def __init__(self, value, emoji, description):
        self.value = value
        self.emoji = emoji
        self.description = description

class MessageType(Enum):
    """Message types for AI processing"""
    TRANSFORM = "transform"  # User wants to send something better
    INTERPRET = "interpret"  # User received something and needs help understanding

# ==========================================
# DATA MODELS SECTION
# ==========================================

@dataclass
class Contact:
    """Contact data model"""
    id: str
    name: str
    context: str
    user_id: str
    created_at: datetime
    updated_at: datetime

@dataclass
class Message:
    """Message data model"""
    id: str
    contact_id: str
    contact_name: str
    type: str
    original: str
    result: Optional[str]
    sentiment: Optional[str]
    emotional_state: Optional[str]
    model: Optional[str]
    healing_score: Optional[int]
    user_id: str
    created_at: datetime

@dataclass
class AIResponse:
    """AI response data model"""
    transformed_message: str
    healing_score: int
    sentiment: str
    emotional_state: str
    explanation: str
    subtext: str = ""
    needs: List[str] = None
    warnings: List[str] = None

# ==========================================
# DATABASE WRAPPER SECTION
# ==========================================

class DatabaseManager:
    """Supabase database wrapper with error handling"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            AppConfig.SUPABASE_URL,
            AppConfig.SUPABASE_KEY
        )
    
    def get_user_contacts(self, user_id: str) -> List[Contact]:
        """Get all contacts for a user"""
        try:
            response = self.supabase.table("contacts").select("*").eq("user_id", user_id).execute()
            contacts = []
            for contact_data in response.data:
                contacts.append(Contact(
                    id=contact_data["id"],
                    name=contact_data["name"],
                    context=contact_data["context"],
                    user_id=contact_data["user_id"],
                    created_at=datetime.fromisoformat(contact_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(contact_data["updated_at"].replace('Z', '+00:00'))
                ))
            return contacts
        except Exception as e:
            st.error(f"Error fetching contacts: {str(e)}")
            return []
    
    def create_contact(self, name: str, context: str, user_id: str) -> Optional[Contact]:
        """Create a new contact"""
        try:
            contact_data = {
                "name": name,
                "context": context,
                "user_id": user_id
            }
            response = self.supabase.table("contacts").insert(contact_data).execute()
            if response.data:
                data = response.data[0]
                return Contact(
                    id=data["id"],
                    name=data["name"],
                    context=data["context"],
                    user_id=data["user_id"],
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
                )
            return None
        except Exception as e:
            st.error(f"Error creating contact: {str(e)}")
            return None
    
    def save_message(self, contact_id: str, contact_name: str, message_type: str,
                    original: str, result: str, user_id: str, ai_response: AIResponse) -> bool:
        """Save a message to the database"""
        try:
            message_data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "type": message_type,
                "original": original,
                "result": result,
                "sentiment": ai_response.sentiment,
                "emotional_state": ai_response.emotional_state,
                "model": AppConfig.AI_MODEL,
                "healing_score": ai_response.healing_score,
                "user_id": user_id
            }
            response = self.supabase.table("messages").insert(message_data).execute()
            return len(response.data) > 0
        except Exception as e:
            st.error(f"Error saving message: {str(e)}")
            return False
    
    def get_conversation_history(self, contact_id: str, user_id: str) -> List[Message]:
        """Get conversation history for a contact"""
        try:
            response = (self.supabase.table("messages")
                       .select("*")
                       .eq("contact_id", contact_id)
                       .eq("user_id", user_id)
                       .order("created_at", desc=True)
                       .limit(50)
                       .execute())
            
            messages = []
            for msg_data in response.data:
                messages.append(Message(
                    id=msg_data["id"],
                    contact_id=msg_data["contact_id"],
                    contact_name=msg_data["contact_name"],
                    type=msg_data["type"],
                    original=msg_data["original"],
                    result=msg_data.get("result"),
                    sentiment=msg_data.get("sentiment"),
                    emotional_state=msg_data.get("emotional_state"),
                    model=msg_data.get("model"),
                    healing_score=msg_data.get("healing_score"),
                    user_id=msg_data["user_id"],
                    created_at=datetime.fromisoformat(msg_data["created_at"].replace('Z', '+00:00'))
                ))
            return messages
        except Exception as e:
            st.error(f"Error fetching conversation history: {str(e)}")
            return []
    
    def save_feedback(self, user_id: str, rating: int, feedback_text: str, feature_context: str) -> bool:
        """Save user feedback"""
        try:
            feedback_data = {
                "user_id": user_id,
                "rating": rating,
                "feedback_text": feedback_text,
                "feature_context": feature_context
            }
            response = self.supabase.table("feedback").insert(feedback_data).execute()
            return len(response.data) > 0
        except Exception as e:
            st.error(f"Error saving feedback: {str(e)}")
            return False
    
    def check_cache(self, contact_id: str, message_hash: str, user_id: str) -> Optional[AIResponse]:
        """Check if we have a cached response"""
        try:
            response = (self.supabase.table("ai_response_cache")
                       .select("*")
                       .eq("contact_id", contact_id)
                       .eq("message_hash", message_hash)
                       .eq("user_id", user_id)
                       .gt("expires_at", datetime.now().isoformat())
                       .execute())
            
            if response.data:
                data = response.data[0]
                return AIResponse(
                    transformed_message=data["response"],
                    healing_score=data["healing_score"],
                    sentiment=data["sentiment"],
                    emotional_state=data["emotional_state"],
                    explanation="From cache"
                )
            return None
        except:
            return None
    
    def save_to_cache(self, contact_id: str, message_hash: str, context: str,
                     response: str, user_id: str, ai_response: AIResponse) -> bool:
        """Save response to cache"""
        try:
            cache_data = {
                "contact_id": contact_id,
                "message_hash": message_hash,
                "context": context,
                "response": response,
                "healing_score": ai_response.healing_score,
                "model": AppConfig.AI_MODEL,
                "sentiment": ai_response.sentiment,
                "emotional_state": ai_response.emotional_state,
                "user_id": user_id,
                "expires_at": (datetime.now() + timedelta(days=AppConfig.CACHE_EXPIRY_DAYS)).isoformat()
            }
            response = self.supabase.table("ai_response_cache").insert(cache_data).execute()
            return len(response.data) > 0
        except:
            return False

# ==========================================
# AI ENGINE SECTION
# ==========================================

class AIEngine:
    """AI processing engine using OpenRouter"""
    
    def __init__(self):
        self.client = openai.OpenAI(
            base_url=AppConfig.OPENROUTER_BASE_URL,
            api_key=AppConfig.OPENROUTER_API_KEY,
        )
    
    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a hash for caching purposes"""
        combined = f"{message}_{contact_context}_{message_type}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_system_prompt(self, message_type: str, relationship_context: str) -> str:
        """Get system prompt based on message type and context"""
        
        base_context = f"""You are The Third Voice - an AI relationship counselor helping people communicate with healing instead of harm. 

RELATIONSHIP CONTEXT: {relationship_context}

Your mission: Transform difficult conversations into opportunities for connection and understanding."""

        if message_type == MessageType.TRANSFORM.value:
            return base_context + """

TRANSFORM MODE: The user wants to say something but needs help saying it better.

Your task:
1. Rewrite their message to be more loving, constructive, and healing
2. Remove blame, criticism, and defensive language
3. Focus on feelings, needs, and requests rather than accusations
4. Add empathy and understanding

RESPONSE FORMAT (JSON):
{
  "transformed_message": "The rewritten message that promotes healing",
  "healing_score": 8,
  "sentiment": "positive/neutral/negative",
  "emotional_state": "frustrated/sad/angry/hopeful/etc",
  "explanation": "Brief explanation of what was changed and why"
}

Keep the transformed message authentic to their feelings but expressed with love."""

        else:  # INTERPRET mode
            return base_context + """

INTERPRET MODE: The user received a difficult message and needs help understanding it.

Your task:
1. Look beyond the surface words to understand the deeper emotional needs
2. Identify what the person is really trying to communicate
3. Suggest a healing response that addresses their underlying needs
4. Point out any relationship patterns or concerning signs

RESPONSE FORMAT (JSON):
{
  "transformed_message": "A suggested loving response to their message",
  "healing_score": 6,
  "sentiment": "positive/neutral/negative", 
  "emotional_state": "hurt/defensive/overwhelmed/etc",
  "explanation": "What they're really trying to say beneath the words",
  "subtext": "The emotional needs and feelings behind their message",
  "needs": ["connection", "understanding", "respect"],
  "warnings": ["This sounds like a pattern of...", "Be aware that..."]
}

Help them respond with empathy while protecting their own emotional wellbeing."""

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db: DatabaseManager) -> AIResponse:
        """Process a message with AI and return structured response"""
        
        # Check cache first
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        if cached_response:
            return cached_response
        
        try:
            # Get relationship context description
            context_desc = "general relationship"
            for rel_context in RelationshipContext:
                if rel_context.value == contact_context:
                    context_desc = rel_context.description.lower()
                    break
            
            system_prompt = self._get_system_prompt(message_type, context_desc)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=AppConfig.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=AppConfig.MAX_TOKENS,
                temperature=AppConfig.TEMPERATURE
            )
            
            # Parse response
            ai_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                ai_data = json.loads(ai_text)
            except json.JSONDecodeError:
                # Fallback for non-JSON responses
                ai_data = {
                    "transformed_message": ai_text,
                    "healing_score": 5,
                    "sentiment": "neutral",
                    "emotional_state": "unclear",
                    "explanation": "Response generated successfully"
                }
            
            # Create structured response
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", ai_text),
                healing_score=ai_data.get("healing_score", 5),
                sentiment=ai_data.get("sentiment", "neutral"),
                emotional_state=ai_data.get("emotional_state", "unclear"),
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            # Cache the response
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            return ai_response
            
        except Exception as e:
            st.error(f"AI processing error: {str(e)}")
            # Return a fallback response
            return AIResponse(
                transformed_message="I'm having trouble processing this message right now. Please try again.",
                healing_score=1,
                sentiment="neutral",
                emotional_state="error",
                explanation="Technical error occurred during processing"
            )

# ==========================================
# AUTHENTICATION SECTION
# ==========================================

class AuthManager:
    """Handle authentication workflows"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.supabase = db.supabase
    
    def sign_up(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                return True, "Check your email for verification link!"
            else:
                return False, "Sign up failed"
                
        except Exception as e:
            return False, f"Sign up error: {str(e)}"
    
    def sign_in(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign in user"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                st.session_state.user = response.user
                return True, "Successfully signed in!"
            else:
                return False, "Invalid credentials"
                
        except Exception as e:
            return False, f"Sign in error: {str(e)}"
    
    def sign_out(self):
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
        except Exception as e:
            st.error(f"Sign out error: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return hasattr(st.session_state, 'user') and st.session_state.user is not None
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.is_authenticated():
            return st.session_state.user.id
        return None

# ==========================================
# UI COMPONENTS SECTION
# ==========================================

class UIComponents:
    """Reusable UI components"""
    
    @staticmethod
    def render_header():
        """Render app header"""
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #2E86AB; margin-bottom: 0;'>🎙️ The Third Voice AI</h1>
            <p style='color: #666; font-style: italic; margin-top: 0;'>
                When both people are speaking from pain, someone must be the third voice
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_mobile_header():
        """Render mobile-optimized header"""
        st.markdown("""
        <div style='text-align: center; padding: 0.5rem 0;'>
            <h2 style='color: #2E86AB; margin: 0;'>🎙️ Third Voice</h2>
            <p style='color: #666; font-size: 0.9rem; margin: 0;'>
                Healing conversations with AI
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_relationship_selector() -> Tuple[str, str]:
        """Render relationship context selector"""
        st.subheader("👥 Who do you need help communicating with?")
        
        # Create options
        options = []
        values = []
        for context in RelationshipContext:
            options.append(f"{context.emoji} {context.description}")
            values.append(context.value)
        
        selected_idx = st.selectbox(
            "Relationship type:",
            range(len(options)),
            format_func=lambda x: options[x],
            key="relationship_selector"
        )
        
        return values[selected_idx], options[selected_idx]
    
    @staticmethod
    def render_healing_score(score: int):
        """Render healing score visualization"""
        # Create stars based on score (1-10 scale to 1-5 stars)
        stars = "⭐" * min(5, max(1, score // 2))
        color = "#4CAF50" if score >= 7 else "#FF9800" if score >= 4 else "#F44336"
        
        st.markdown(f"""
        <div style='background: {color}20; padding: 0.5rem; border-radius: 8px; text-align: center;'>
            <strong>Healing Score: {score}/10</strong><br>
            {stars}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_feedback_form(feature_context: str) -> Optional[Tuple[int, str]]:
        """Render feedback form"""
        with st.expander("💬 How was this helpful?"):
            rating = st.slider("Rating", 1, 5, 3, key=f"rating_{feature_context}")
            feedback_text = st.text_area(
                "What could be better?", 
                placeholder="Your feedback helps us improve...",
                key=f"feedback_{feature_context}"
            )
            
            if st.button("Submit Feedback", key=f"submit_{feature_context}"):
                return rating, feedback_text
        return None
    
    @staticmethod
    def render_message_history(messages: List[Message]):
        """Render conversation history"""
        if not messages:
            st.info("No previous messages yet")
            return
        
        st.subheader("📝 Recent Conversations")
        
        for msg in messages[:5]:  # Show last 5 messages
            with st.expander(f"{msg.type.title()} - {msg.created_at.strftime('%m/%d %H:%M')}"):
                st.write("**Original:**")
                st.write(msg.original)
                
                if msg.result:
                    st.write("**AI Suggestion:**")
                    st.write(msg.result)
                    
                    if msg.healing_score:
                        UIComponents.render_healing_score(msg.healing_score)

# ==========================================
# PAGE LAYOUTS SECTION
# ==========================================

class OnboardingFlow:
    """First-time user onboarding"""
    
    def __init__(self, db: DatabaseManager, ai_engine: AIEngine):
        self.db = db
        self.ai_engine = ai_engine
    
    def run(self, user_id: str) -> bool:
        """Run onboarding flow, return True if completed"""
        
        # Initialize onboarding state
        if 'onboarding_step' not in st.session_state:
            st.session_state.onboarding_step = 1
        
        if st.session_state.onboarding_step == 1:
            return self._step_1_welcome()
        elif st.session_state.onboarding_step == 2:
            return self._step_2_context(user_id)
        elif st.session_state.onboarding_step == 3:
            return self._step_3_problem()
        elif st.session_state.onboarding_step == 4:
            return self._step_4_ai_magic(user_id)
        elif st.session_state.onboarding_step == 5:
            return self._step_5_feedback(user_id)
        
        return True
    
    def _step_1_welcome(self) -> bool:
        """Welcome step"""
        UIComponents.render_header()
        
        st.markdown("""
        ### 🌟 Transform Difficult Conversations with AI
        
        Welcome to The Third Voice - your AI relationship counselor that helps you:
        
        - 💬 **Transform** harsh words into healing messages
        - 🤔 **Interpret** what people really mean when they're upset
        - ❤️ **Heal** relationships through better communication
        
        Let's try it out with someone in your life...
        """)
        
        if st.button("Let's Start!", use_container_width=True, type="primary"):
            st.session_state.onboarding_step = 2
            st.rerun()
        
        return False
    
    def _step_2_context(self, user_id: str) -> bool:
        """Context selection step"""
        UIComponents.render_mobile_header()
        
        st.markdown("### Step 1: Choose Your Relationship")
        
        name = st.text_input(
            "What's their name?",
            placeholder="e.g., Sarah, Mom, Boss...",
            key="onboarding_name"
        )
        
        context_value, context_display = UIComponents.render_relationship_selector()
        
        if name and st.button("Continue", use_container_width=True, type="primary"):
            # Store the contact info
            st.session_state.onboarding_contact = {
                "name": name,
                "context": context_value,
                "context_display": context_display
            }
            st.session_state.onboarding_step = 3
            st.rerun()
        
        return False
    
    def _step_3_problem(self) -> bool:
        """Problem input step"""
        UIComponents.render_mobile_header()
        
        contact = st.session_state.onboarding_contact
        st.markdown(f"### Step 2: What Happened with {contact['name']}?")
        
        # Choose transform or interpret
        mode = st.radio(
            "Choose your situation:",
            [
                "💬 I want to say something but need help saying it better",
                "🤔 They said something and I need help understanding it"
            ],
            key="onboarding_mode"
        )
        
        if "I want to say" in mode:
            message_type = MessageType.TRANSFORM.value
            placeholder = f"What do you want to tell {contact['name']}?\n\nExample: 'I'm frustrated that you never help with chores'"
        else:
            message_type = MessageType.INTERPRET.value
            placeholder = f"What did {contact['name']} say to you?\n\nExample: 'You never appreciate anything I do!'"
        
        message = st.text_area(
            "Share the message:",
            placeholder=placeholder,
            height=150,
            key="onboarding_message"
        )
        
        if message and st.button("Get AI Help", use_container_width=True, type="primary"):
            st.session_state.onboarding_message_data = {
                "message": message,
                "type": message_type
            }
            st.session_state.onboarding_step = 4
            st.rerun()
        
        return False
    
    def _step_4_ai_magic(self, user_id: str) -> bool:
        """AI processing step"""
        UIComponents.render_mobile_header()
        
        contact = st.session_state.onboarding_contact
        message_data = st.session_state.onboarding_message_data
        
        st.markdown(f"### Step 3: AI Magic ✨")
        
        # Create temporary contact for demo
        temp_contact_id = str(uuid.uuid4())
        
        with st.spinner("The Third Voice is thinking..."):
            # Process with AI
            ai_response = self.ai_engine.process_message(
                message_data["message"],
                contact["context"],
                message_data["type"],
                temp_contact_id,
                user_id
            )
        
        # Display results
        if message_data["type"] == MessageType.TRANSFORM.value:
            st.success("Here's how to say it with love:")
        else:
            st.success("Here's what they really mean and how to respond:")
        
        st.markdown(f"""
        <div style='background: #f0f8ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #2E86AB;'>
            {ai_response.transformed_message}
        </div>
        """, unsafe_allow_html=True)
        
        UIComponents.render_healing_score(ai_response.healing_score)
        
        if ai_response.explanation:
            with st.expander("💡 Why this works better"):
                st.write(ai_response.explanation)
        
        if ai_response.subtext:
            with st.expander("🎯 What they're really feeling"):
                st.write(ai_response.subtext)
        
        if ai_response.needs:
            with st.expander("💚 Their underlying needs"):
                for need in ai_response.needs:
                    st.write(f"• {need}")
        
        # Store AI response for next step
        st.session_state.onboarding_ai_response = ai_response
        
        if st.button("This is Amazing! Continue", use_container_width=True, type="primary"):
            st.session_state.onboarding_step = 5
            st.rerun()
        
        return False
    
    def _step_5_feedback(self, user_id: str) -> bool:
        """Feedback and completion step"""
        UIComponents.render_mobile_header()
        
        st.markdown("### Step 4: Help Us Improve")
        
        # Quick feedback
        rating = st.slider("How helpful was this?", 1, 5, 4, key="onboarding_rating")
        feedback_text = st.text_area(
            "What could be better?",
            placeholder="Your feedback helps us improve...",
            key="onboarding_feedback"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Skip", use_container_width=True):
                return self._complete_onboarding(user_id)
        
        with col2:
            if st.button("Submit & Continue", use_container_width=True, type="primary"):
                # Save feedback
                self.db.save_feedback(user_id, rating, feedback_text, "onboarding")
                return self._complete_onboarding(user_id)
        
        return False
    
    def _complete_onboarding(self, user_id: str) -> bool:
        """Complete onboarding and create real contact"""
        
        # Create the actual contact
        contact_data = st.session_state.onboarding_contact
        contact = self.db.create_contact(
            contact_data["name"],
            contact_data["context"],
            user_id
        )
        
        if contact:
            # Save the demo message if it was successful
            if hasattr(st.session_state, 'onboarding_ai_response'):
                message_data = st.session_state.onboarding_message_data
                ai_response = st.session_state.onboarding_ai_response
                
                self.db.save_message(
                    contact.id,
                    contact.name,
                    message_data["type"],
                    message_data["message"],
                    ai_response.transformed_message,
                    user_id,
                    ai_response
                )
        
        # Clear onboarding data
