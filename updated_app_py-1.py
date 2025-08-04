"""
The Third Voice AI - Entry Point
Streamlit application for family communication healing
"""

import streamlit as st
import hashlib
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import requests
import time
import uuid
from supabase import create_client, Client

# Import modularized components
from src.config.settings import AppConfig, init_app_config
from src.core.ai_engine import AIEngine, MessageType, RelationshipContext
from src.data.models import Contact, Message, AIResponse

# Initialize configuration
init_app_config()

# ==========================================
# DATABASE WRAPPER SECTION (TO BE MODULARIZED NEXT)
# ==========================================

class DatabaseManager:
    """Supabase database wrapper with error handling"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            AppConfig.get_supabase_url(),
            AppConfig.get_supabase_key()
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
# AUTHENTICATION SECTION (TO BE MODULARIZED)
# ==========================================

class AuthManager:
    """Handle authentication workflows"""
    
    def __init__(self, db):
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
# UI COMPONENTS SECTION (TO BE MODULARIZED)
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
# REMAINING SECTIONS (TO BE MODULARIZED)
# ==========================================

# ... [Rest of the original code remains the same for now] ...

class OnboardingFlow:
    """First-time user onboarding"""
    
    def __init__(self, db, ai_engine):
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
                user_id,
                self.db
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
        for key in list(st.session_state.keys()):
            if key.startswith('onboarding_'):
                del st.session_state[key]
        
        # Mark as completed
        st.session_state.onboarding_completed = True
        st.session_state.selected_contact = contact
        
        st.success("🎉 Welcome to The Third Voice! Your contact has been saved.")
        st.balloons()
        
        return True

class Dashboard:
    """Main dashboard after onboarding"""
    
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai_engine = ai_engine
    
    def run(self, user_id: str):
        """Run main dashboard"""
        
        # Get user's contacts
        contacts = self.db.get_user_contacts(user_id)
        
        if not contacts:
            # No contacts yet, show add contact flow
            self._render_add_first_contact(user_id)
        else:
            # Show contacts and conversation interface
            self._render_main_interface(user_id, contacts)
    
    def _render_add_first_contact(self, user_id: str):
        """Render interface to add first contact"""
        UIComponents.render_header()
        
        st.markdown("""
        ### 👥 Add Your First Contact
        
        Start by adding someone you'd like to communicate better with.
        """)
        
        with st.form("add_contact_form"):
            name = st.text_input("Name", placeholder="e.g., Sarah, Mom, Boss...")
            context_value, context_display = UIComponents.render_relationship_selector()
            
            if st.form_submit_button("Add Contact", use_container_width=True, type="primary"):
                if name:
                    contact = self.db.create_contact(name, context_value, user_id)
                    if contact:
                        st.session_state.selected_contact = contact
                        st.success(f"Added {name} successfully!")
                        st.rerun()
                else:
                    st.error("Please enter a name")
    
    def _render_main_interface(self, user_id: str, contacts: List[Contact]):
        """Render main interface with contacts and conversation"""
        
        # Mobile-optimized layout
        UIComponents.render_mobile_header()
        
        # Contact selection
        if len(contacts) == 1:
            selected_contact = contacts[0]
            st.session_state.selected_contact = selected_contact
        else:
            # Multiple contacts - show selector
            contact_names = [f"{c.name} ({RelationshipContext(c.context).emoji})" for c in contacts]
            selected_idx = st.selectbox(
                "Choose contact:",
                range(len(contacts)),
                format_func=lambda x: contact_names[x],
                key="contact_selector"
            )
            selected_contact = contacts[selected_idx]
            st.session_state.selected_contact = selected_contact
        
        # Main conversation interface
        self._render_conversation_interface(user_id, selected_contact)
        
        # Add new contact button
        if st.button("➕ Add Another Contact", use_container_width=True):
            st.session_state.show_add_contact = True
            st.rerun()
        
        # Handle add contact modal
        if st.session_state.get('show_add_contact', False):
            self._render_add_contact_modal(user_id)
    
    def _render_conversation_interface(self, user_id: str, contact: Contact):
        """Render the main conversation interface"""
        
        # Contact header
        context_emoji = RelationshipContext(contact.context).emoji
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <h3 style='margin: 0; color: #2E86AB;'>{context_emoji} {contact.name}</h3>
            <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                {RelationshipContext(contact.context).description}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mode selection
        st.subheader("🎯 What do you need help with?")
        
        mode = st.radio(
            "Choose your situation:",
            [
                "💬 Transform: I want to say something better",
                "🤔 Interpret: Help me understand what they meant"
            ],
            key=f"mode_{contact.id}"
        )
        
        message_type = MessageType.TRANSFORM.value if "Transform" in mode else MessageType.INTERPRET.value
        
        # Message input
        if message_type == MessageType.TRANSFORM.value:
            placeholder = f"What do you want to tell {contact.name}?\n\nExample: 'I'm frustrated that you're always late'"
            helper_text = "💡 Share what you want to say, and I'll help you say it with love"
        else:
            placeholder = f"What did {contact.name} say to you?\n\nExample: 'You never listen to me!'"
            helper_text = "💡 Share what they said, and I'll help you understand what they really mean"
        
        st.write(helper_text)
        
        message = st.text_area(
            "Your message:",
            placeholder=placeholder,
            height=120,
            key=f"message_input_{contact.id}"
        )
        
        # Process button
        if st.button("🎙️ Get Third Voice Help", use_container_width=True, type="primary", disabled=not message):
            self._process_message(user_id, contact, message, message_type)
        
        # Show conversation history
        self._render_conversation_history(user_id, contact)
    
    def _process_message(self, user_id: str, contact: Contact, message: str, message_type: str):
        """Process message with AI"""
        
        with st.spinner("The Third Voice is thinking..."):
            ai_response = self.ai_engine.process_message(
                message, contact.context, message_type, contact.id, user_id, self.db
            )
        
        # Display results
        if message_type == MessageType.TRANSFORM.value:
            st.success("🌟 Here's how to say it with love:")
        else:
            st.success("🎯 Here's what they really mean and how to respond:")
        
        # Main response
        st.markdown(f"""
        <div style='background: #f0f8ff; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #2E86AB; margin: 1rem 0;'>
            <h4 style='margin-top: 0; color: #2E86AB;'>💬 Suggested Message:</h4>
            <p style='margin-bottom: 0; font-size: 1.1rem; line-height: 1.6;'>{ai_response.transformed_message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Healing score
        UIComponents.render_healing_score(ai_response.healing_score)
        
        # Additional insights
        col1, col2 = st.columns(2)
        
        with col1:
            if ai_response.explanation:
                with st.expander("💡 Why this works better"):
                    st.write(ai_response.explanation)
        
        with col2:
            if ai_response.emotional_state != "unclear":
                with st.expander(f"😊 Emotional tone: {ai_response.emotional_state}"):
                    st.write(f"The overall emotional tone detected: **{ai_response.emotional_state}**")
        
        # Interpret mode specific insights
        if message_type == MessageType.INTERPRET.value:
            if ai_response.subtext:
                with st.expander("🎯 What they're really feeling"):
                    st.write(ai_response.subtext)
            
            if ai_response.needs:
                with st.expander("💚 Their underlying needs"):
                    for need in ai_response.needs:
                        st.write(f"• {need.title()}")
            
            if ai_response.warnings:
                with st.expander("⚠️ Things to be aware of"):
                    for warning in ai_response.warnings:
                        st.warning(warning)
        
        # Save to database
        success = self.db.save_message(
            contact.id, contact.name, message_type, message, 
            ai_response.transformed_message, user_id, ai_response
        )
        
        if success:
            st.success("💾 Conversation saved!")
        
        # Feedback form
        feedback_result = UIComponents.render_feedback_form(f"conversation_{contact.id}")
        if feedback_result:
            rating, feedback_text = feedback_result
            if self.db.save_feedback(user_id, rating, feedback_text, "conversation"):
                st.success("Thank you for your feedback!")
                st.rerun()
    
    def _render_conversation_history(self, user_id: str, contact: Contact):
        """Render conversation history for the selected contact"""
        
        messages = self.db.get_conversation_history(contact.id, user_id)
        
        if messages:
            st.markdown("---")
            UIComponents.render_message_history(messages)
    
    def _render_add_contact_modal(self, user_id: str):
        """Render modal to add new contact"""
        
        st.markdown("### ➕ Add New Contact")
        
        with st.form("add_new_contact"):
            name = st.text_input("Name", placeholder="e.g., Sarah, Mom, Boss...")
            context_value, context_display = UIComponents.render_relationship_selector()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_add_contact = False
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Add Contact", use_container_width=True, type="primary"):
                    if name:
                        contact = self.db.create_contact(name, context_value, user_id)
                        if contact:
                            st.session_state.selected_contact = contact
                            st.session_state.show_add_contact = False
                            st.success(f"Added {name} successfully!")
                            st.rerun()
                    else:
                        st.error("Please enter a name")

class AuthenticationUI:
    """Authentication user interface"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
    
    def run(self) -> bool:
        """Run authentication flow, return True if authenticated"""
        
        if self.auth_manager.is_authenticated():
            return True
        
        UIComponents.render_header()
        
        # Check URL params for verification (using newer API)
        try:
            query_params = st.query_params
            if 'type' in query_params and query_params['type'] == 'signup':
                st.success("✅ Email verified! Please sign in below.")
        except:
            # Fallback for older Streamlit versions
            try:
                query_params = st.experimental_get_query_params()
                if 'type' in query_params and query_params['type'][0] == 'signup':
                    st.success("✅ Email verified! Please sign in below.")
            except:
                pass
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            self._render_sign_in_form()
        
        with tab2:
            self._render_sign_up_form()
        
        return False
    
    def _render_sign_in_form(self):
        """Render sign in form"""
        
        st.subheader("Welcome Back")
        
        with st.form("sign_in_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                if email and password:
                    success, message = self.auth_manager.sign_in(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    def _render_sign_up_form(self):
        """Render sign up form"""
        
        st.subheader("Create Account")
        st.markdown("Join thousands healing their relationships with AI")
        
        with st.form("sign_up_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", help="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords don't match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = self.auth_manager.sign_up(email, password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

# ==========================================
# MAIN APPLICATION CONTROLLER
# ==========================================

class ThirdVoiceApp:
    """Main application controller"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.ai_engine = AIEngine()
        self.auth_manager = AuthManager(self.db)
        self.auth_ui = AuthenticationUI(self.auth_manager)
        self.onboarding = OnboardingFlow(self.db, self.ai_engine)
        self.dashboard = Dashboard(self.db, self.ai_engine)
    
    def run(self):
        """Main application entry point"""
        
        # Load custom CSS for mobile optimization
        self._load_custom_css()
        
        # Authentication check
        if not self.auth_ui.run():
            return
        
        # Get current user
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            st.error("Authentication error. Please refresh the page.")
            return
        
        # Add sign out button to sidebar
        with st.sidebar:
            st.markdown("---")
            if st.button("Sign Out", use_container_width=True):
                self.auth_manager.sign_out()
                st.rerun()
        
        # Check if user needs onboarding
        if not st.session_state.get('onboarding_completed', False):
            contacts = self.db.get_user_contacts(user_id)
            if not contacts:
                # First time user - run onboarding
                if self.onboarding.run(user_id):
                    st.rerun()
                return
            else:
                # Has contacts but hasn't seen onboarding completion
                st.session_state.onboarding_completed = True
        
        # Run main dashboard
        self.dashboard.run(user_id)
    
    def _load_custom_css(self):
        """Load custom CSS for mobile optimization"""
        
        st.markdown("""
        <style>
        /* Mobile-first responsive design */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Mobile optimization */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            /* Make buttons more touch-friendly */
            .stButton > button {
                height: 3rem;
                font-size: 1.1rem;
            }
            
            /* Optimize text areas for mobile */
            .stTextArea > div > div > textarea {
                font-size: 1rem;
            }
            
            /* Responsive columns */
            .row-widget.stRadio > div {
                flex-direction: column;
            }
        }
        
        /* Custom styling */
        .stSelectbox > div > div {
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #2E86AB;
            box-shadow: 0 0 0 0.2rem rgba(46, 134, 171, 0.25);
        }
        
        /* Healing score styling */
        .metric-container {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Success message styling */
        .stSuccess {
            border-radius: 8px;
        }
        
        /* Warning message styling */
        .stWarning {
            border-radius: 8px;
        }
        
        /* Error message styling */
        .stError {
            border-radius: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# APPLICATION ENTRY POINT
# ==========================================

def main():
    """Application entry point"""
    try:
        app = ThirdVoiceApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        # Log the full traceback for debugging
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()