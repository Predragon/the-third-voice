"""
UI Pages Module for The Third Voice AI
Contains all page-level UI components and flows
"""

import streamlit as st
import uuid
from typing import List, Optional, Tuple
from ..core.ai_engine import MessageType, RelationshipContext
from ..data.models import Contact, Message
from .components import UIComponents


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
        
        # Display results using UIComponents
        UIComponents.render_ai_response(ai_response, message_data["type"])
        
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
        context_enum = RelationshipContext(contact.context)
        UIComponents.render_contact_header(contact, context_enum)
        
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
        
        # Display results using UIComponents
        UIComponents.render_ai_response(ai_response, message_type)
        
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
