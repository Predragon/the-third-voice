"""
Updated Dashboard Class with Enhanced Sidebar Integration
Main dashboard after onboarding with better session management
"""

import streamlit as st
import uuid
from typing import List, Optional, Tuple
from ..core.ai_engine import MessageType, RelationshipContext
from ..data.models import Contact, Message
from .components import UIComponents


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