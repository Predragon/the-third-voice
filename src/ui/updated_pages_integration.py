"""
UI Pages Module for The Third Voice AI
Contains all page-level UI components and flows
Enhanced with better logout functionality and updated Dashboard
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
    
    def run(self, user_id: str, auth_manager) -> bool:
        """Run onboarding flow, return True if completed"""
        
        # Initialize onboarding state
        if 'onboarding_step' not in st.session_state:
            st.session_state.onboarding_step = 1
        
        # Render logout in header for all onboarding steps
        UIComponents.render_header_with_logout(auth_manager)
        
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
    """Main dashboard after onboarding with enhanced sidebar"""
    
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai_engine = ai_engine
    
    def run(self, user_id: str, auth_manager):
        """Run main dashboard with enhanced sidebar"""
        
        # Get user's contacts
        contacts = self.db.get_user_contacts(user_id)
        
        if not contacts:
            # No contacts yet, show add contact flow
            self._render_add_first_contact(user_id, auth_manager)
        else:
            # Show enhanced interface with sidebar
            self._render_enhanced_interface(user_id, contacts, auth_manager)
    
    def _render_add_first_contact(self, user_id: str, auth_manager):
        """Render interface to add first contact"""
        
        # Enhanced sidebar even for first contact
        UIComponents.render_enhanced_sidebar(auth_manager, [], None, self.db, user_id)
        
        # Main content
        UIComponents.render_mobile_header()
        
        st.markdown("""
        ### 👥 Welcome! Add Your First Contact
        
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
    
    def _render_enhanced_interface(self, user_id: str, contacts: List[Contact], auth_manager):
        """Render enhanced interface with sidebar navigation"""
        
        # Determine current contact
        current_contact = st.session_state.get('selected_contact')
        
        # If no contact selected or selected contact doesn't exist, pick first one
        if not current_contact or not any(c.id == current_contact.id for c in contacts):
            current_contact = contacts[0]
            st.session_state.selected_contact = current_contact
        
        # Render enhanced sidebar with all features
        UIComponents.render_enhanced_sidebar(
            auth_manager, 
            contacts, 
            current_contact, 
            self.db, 
            user_id
        )
        
        # Main content area
        UIComponents.render_mobile_header()
        
        # Handle quick actions from sidebar
        if st.session_state.get('quick_action'):
            self._handle_quick_action(user_id, current_contact)
        
        # Main conversation interface
        self._render_conversation_interface(user_id, current_contact)
        
        # Handle add contact modal from sidebar
        if st.session_state.get('show_add_contact', False):
            self._render_add_contact_modal(user_id)
    
    def _handle_quick_action(self, user_id: str, contact: Contact):
        """Handle quick actions triggered from sidebar"""
        
        quick_action = st.session_state.get('quick_action')
        
        if quick_action == "transform":
            st.info("💬 Transform Mode: Enter a message you want to say more lovingly")
            st.session_state.force_mode = MessageType.TRANSFORM.value
        elif quick_action == "interpret":
            st.info("🤔 Interpret Mode: Enter a message you received and need help understanding")
            st.session_state.force_mode = MessageType.INTERPRET.value
        
        # Clear the quick action
        if 'quick_action' in st.session_state:
            del st.session_state['quick_action']
    
    def _render_conversation_interface(self, user_id: str, contact: Contact):
        """Render the main conversation interface with enhanced features"""
        
        # Contact header
        context_enum = RelationshipContext(contact.context)
        UIComponents.render_contact_header(contact, context_enum)
        
        # Mode selection (with quick action override)
        forced_mode = st.session_state.get('force_mode')
        
        if forced_mode:
            # Use forced mode from quick action
            if forced_mode == MessageType.TRANSFORM.value:
                mode_display = "💬 Transform: I want to say something better"
                message_type = MessageType.TRANSFORM.value
            else:
                mode_display = "🤔 Interpret: Help me understand what they meant"
                message_type = MessageType.INTERPRET.value
            
            st.markdown(f"**Selected Mode:** {mode_display}")
            
            if st.button("↩️ Change Mode", key="change_mode"):
                if 'force_mode' in st.session_state:
                    del st.session_state['force_mode']
                st.rerun()
        else:
            # Normal mode selection
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
        
        # Message input with context-aware placeholders
        if message_type == MessageType.TRANSFORM.value:
            placeholder = f"What do you want to tell {contact.name}?\n\nExample: 'I'm frustrated that you're always late'"
            helper_text = "💡 Share what you want to say, and I'll help you say it with love"
            button_text = "🌟 Transform My Message"
        else:
            placeholder = f"What did {contact.name} say to you?\n\nExample: 'You never listen to me!'"
            helper_text = "💡 Share what they said, and I'll help you understand what they really mean"
            button_text = "🎯 Help Me Understand"
        
        st.write(helper_text)
        
        message = st.text_area(
            "Your message:",
            placeholder=placeholder,
            height=120,
            key=f"message_input_{contact.id}_{message_type}"
        )
        
        # Process button with dynamic text
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button(button_text, use_container_width=True, type="primary", disabled=not message):
                self._process_message(user_id, contact, message, message_type)
        
        with col2:
            # Clear message button
            if st.button("🗑️ Clear", use_container_width=True, help="Clear the message"):
                # Force rerun to clear the text area
                st.rerun()
        
        # Show conversation history in collapsible section
        self._render_conversation_history(user_id, contact)
        
        # Clear forced mode after rendering
        if 'force_mode' in st.session_state:
            del st.session_state['force_mode']
    
    def _process_message(self, user_id: str, contact: Contact, message: str, message_type: str):
        """Process message with AI and enhanced feedback"""
        
        # Show processing indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🤖 The Third Voice is analyzing your message...")
            progress_bar.progress(25)
            
            # Process with AI
            ai_response = self.ai_engine.process_message(
                message, contact.context, message_type, contact.id, user_id, self.db
            )
            
            progress_bar.progress(75)
            status_text.text("✨ Crafting your response...")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display results using UIComponents
            UIComponents.render_ai_response(ai_response, message_type)
            
            # Save to database
            success = self.db.save_message(
                contact.id, contact.name, message_type, message, 
                ai_response.transformed_message, user_id, ai_response
            )
            
            if success:
                st.success("💾 Conversation saved to your history!")
            else:
                st.warning("⚠️ Response generated but couldn't save to history")
            
            # Enhanced feedback with contact context
            feedback_result = UIComponents.render_feedback_form(f"conversation_{contact.id}_{message_type}")
            if feedback_result:
                rating, feedback_text = feedback_result
                feedback_context = f"conversation_{message_type}_{contact.context}"
                if self.db.save_feedback(user_id, rating, feedback_text, feedback_context):
                    st.success("🙏 Thank you for your feedback!")
                    st.rerun()
        
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Something went wrong: {str(e)}")
            st.info("💡 Try refreshing the page or contact support if the issue persists")
    
    def _render_conversation_history(self, user_id: str, contact: Contact):
        """Render conversation history for the selected contact"""
        
        messages = self.db.get_conversation_history(contact.id, user_id)
        
        if messages:
            with st.expander(f"📚 Conversation History with {contact.name} ({len(messages)} messages)", expanded=False):
                
                # Filter options
                col1, col2 = st.columns(2)
                
                with col1:
                    show_type = st.selectbox(
                        "Filter by type:",
                        ["All", "Transform", "Interpret"],
                        key=f"history_filter_{contact.id}"
                    )
                
                with col2:
                    show_count = st.selectbox(
                        "Show messages:",
                        [5, 10, 20, "All"],
                        key=f"history_count_{contact.id}"
                    )
                
                # Filter messages
                filtered_messages = messages
                if show_type != "All":
                    filtered_messages = [m for m in messages if m.type.lower() == show_type.lower()]
                
                if show_count != "All":
                    filtered_messages = filtered_messages[:show_count]
                
                # Display filtered messages
                if filtered_messages:
                    for i, msg in enumerate(filtered_messages):
                        with st.container():
                            # Message header
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.write(f"**{msg.type.title()}** - {msg.created_at.strftime('%m/%d %H:%M')}")
                            
                            with col2:
                                if msg.healing_score:
                                    st.write(f"⭐ {msg.healing_score}/10")
                            
                            with col3:
                                if msg.emotional_state:
                                    st.write(f"😊 {msg.emotional_state}")
                            
                            # Message content
                            st.write("**Original:**")
                            st.write(f"_{msg.original}_")
                            
                            if msg.result:
                                st.write("**AI Suggestion:**")
                                st.success(msg.result)
                            
                            if i < len(filtered_messages) - 1:
                                st.markdown("---")
                else:
                    st.info(f"No {show_type.lower()} messages found")
        else:
            st.info("💬 No conversation history yet. Start by sending your first message!")
    
    def _render_add_contact_modal(self, user_id: str):
        """Render modal to add new contact with enhanced features"""
        
        st.markdown("### ➕ Add New Contact")
        st.markdown("Add someone new you'd like to communicate better with.")
        
        with st.form("add_new_contact"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                name = st.text_input("Name", placeholder="e.g., Sarah, Mom, Boss...")
            
            with col2:
                # Quick name suggestions based on context
                if st.button("💡 Suggestions", help="Get name ideas"):
                    suggestions = [
                        "Partner", "Mom", "Dad", "Boss", "Coworker", 
                        "Sister", "Brother", "Friend", "Ex", "Roommate"
                    ]
                    st.write("**Common names:** " + ", ".join(suggestions))
            
            context_value, context_display = UIComponents.render_relationship_selector()
            
            # Optional description
            description = st.text_area(
                "Notes (optional):",
                placeholder="Any context that might help the AI understand your relationship...",
                height=80
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_add_contact = False
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Add Contact", use_container_width=True, type="primary"):
                    if name.strip():
                        contact = self.db.create_contact(name.strip(), context_value, user_id)
                        if contact:
                            st.session_state.selected_contact = contact
                            st.session_state.show_add_contact = False
                            st.success(f"✅ Added {name} successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to create contact. Please try again.")
                    else:
                        st.error("Please enter a name")
