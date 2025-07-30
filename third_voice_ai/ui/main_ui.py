# third_voice_ai/ui/main_ui.py
# Main application UI components for The Third Voice AI

import streamlit as st
from typing import Dict, Any, Optional
from .components import (
    display_error, display_success, show_navigation_button, 
    show_form_input, show_selectbox, show_contact_card,
    show_conversation_message, show_healing_score_display,
    show_copy_button, create_two_column_layout, create_three_column_layout,
    create_metric_card
)
from ..config import CONTEXTS, ENABLE_ANALYTICS, ENABLE_INTERPRETATION, ERROR_MESSAGES
from ..prompts import get_healing_score_explanation
from loguru import logger


class MainUI:
    """Main application UI components and handlers"""
    
    @staticmethod
    def show_sidebar(state_manager, auth_manager) -> None:
        """
        Display application sidebar with navigation and contacts
        
        Args:
            state_manager: State manager instance
            auth_manager: Authentication manager instance
        """
        with st.sidebar:
            st.markdown("### 🎙️ The Third Voice AI")
            user = state_manager.get_user()
            if user:
                st.write(f"**{user.email}**")
            else:
                st.write("**Guest**")
            
            if show_navigation_button("🚪 Logout", "logout_btn"):
                if auth_manager.sign_out():
                    state_manager.clear_authentication()
                    st.rerun()
            
            st.markdown("---")
            st.header("Navigation")
            
            MainUI._show_navigation_links(state_manager)
            
            st.markdown("---")
            st.header("Contacts")
            
            MainUI._show_contacts_sidebar(state_manager)
            
            st.markdown("---")
            MainUI._show_mission_reminder()
    
    @staticmethod
    def show_first_time_setup(state_manager, data_manager) -> None:
        """
        Display first-time setup page
        
        Args:
            state_manager: State manager instance
            data_manager: Data manager instance
        """
        st.markdown("### 🎙️ Welcome to The Third Voice")
        
        # Beta message
        st.info("💙 This tool is in beta — it may not be perfect, but it's built with love, and it listens.")
        
        st.markdown("**Choose a relationship type to get started, or add a custom contact:**")
        
        # Quick context buttons in 2 columns
        cols = st.columns(2)
        contexts_items = list(CONTEXTS.items())
        
        for i, (context_key, context_info) in enumerate(contexts_items):
            with cols[i % 2]:
                if st.button(
                    f"{context_info['icon']} {context_key.title()}\n{context_info['description']}",
                    key=f"context_{context_key}",
                    use_container_width=True
                ):
                    MainUI._handle_quick_contact_creation(context_key, state_manager, data_manager)
        
        st.markdown("---")
        
        # Custom contact form
        MainUI._show_custom_contact_form(state_manager, data_manager, "first_time")
        
        # Welcome message
        MainUI._show_welcome_message()
    
    @staticmethod
    def show_add_contact_page(state_manager, data_manager) -> None:
        """
        Display add contact page
        
        Args:
            state_manager: State manager instance
            data_manager: Data manager instance
        """
        st.markdown("### ➕ Add New Contact")
        
        if show_navigation_button("← Back to Contacts", "back_to_contacts"):
            state_manager.navigate_to("contacts_list")
            state_manager.clear_error()
            st.rerun()
        
        st.markdown("**Tell us about this relationship so we can provide better guidance:**")
        
        MainUI._show_custom_contact_form(state_manager, data_manager, "add_contact")
    
    @staticmethod
    def show_contacts_list(state_manager, data_manager) -> None:
        """
        Display contacts list page
        
        Args:
            state_manager: State manager instance
            data_manager: Data manager instance
        """
        st.markdown("### 🎙️ The Third Voice - Your Contacts")
        
        contacts = state_manager.get_contacts()
        
        if not contacts:
            MainUI._show_empty_contacts_state(state_manager)
            return
        
        # Sort contacts by most recent activity
        sorted_contacts = MainUI._sort_contacts_by_activity(contacts)
        
        st.markdown(f"**{len(sorted_contacts)} contact{'s' if len(sorted_contacts) != 1 else ''}** • Tap to continue conversation")
        
        # Display contacts as buttons with preview
        MainUI._display_contact_buttons(sorted_contacts, state_manager)
        
        st.markdown("---")
        if show_navigation_button("➕ Add New Contact", "add_new_contact_from_list"):
            state_manager.navigate_to("add_contact")
            st.rerun()
    
    @staticmethod
    def show_conversation_interface(state_manager, data_manager, ai_processor) -> None:
        """
        Display conversation interface
        
        Args:
            state_manager: State manager instance
            data_manager: Data manager instance
            ai_processor: AI processor instance
        """
        active_contact = state_manager.get_active_contact()
        if not active_contact:
            display_error(ERROR_MESSAGES["contact_not_found"])
            state_manager.navigate_to("contacts_list")
            st.rerun()
            return
        
        contact_data = state_manager.get_contact_data(active_contact)
        if not contact_data:
            display_error(ERROR_MESSAGES["contact_not_found"])
            state_manager.navigate_to("contacts_list")
            st.rerun()
            return
        
        context = contact_data["context"]
        history = contact_data["history"]
        contact_id = contact_data.get("id")
        
        # Header with edit button
        MainUI._show_conversation_header(state_manager, contact_id, active_contact, context)
        
        # Navigation buttons
        MainUI._show_conversation_navigation(state_manager)
        
        # Relationship progress if available
        if ENABLE_ANALYTICS and history:
            MainUI._show_relationship_progress(ai_processor, history)
        
        st.markdown("---")
        
        # Input section
        MainUI._show_input_section(state_manager, data_manager, ai_processor, active_contact, context, history, contact_id)
        
        st.markdown("---")
        
        # AI Response section
        MainUI._show_ai_response_section(state_manager, active_contact, history)
        
        st.markdown("---")
        
        # Conversation History
        MainUI._show_conversation_history(history)
    
    @staticmethod
    def show_edit_contact_page(state_manager, data_manager) -> None:
        """
        Display edit contact page
        
        Args:
            state_manager: State manager instance
            data_manager: Data manager instance
        """
        edit_contact = state_manager.get_edit_contact()
        if not edit_contact:
            state_manager.navigate_to("contacts_list")
            st.rerun()
            return
        
        st.markdown(f"### ✏️ Edit Contact: {edit_contact['name']}")
        
        if show_navigation_button("← Back", "back_to_conversation"):
            state_manager.navigate_to("conversation")
            state_manager.set_edit_contact(None)
            st.rerun()
        
        MainUI._show_edit_contact_form(edit_contact, state_manager, data_manager)
        
        # Warning about deletion
        st.warning("⚠️ Deleting a contact will permanently remove all conversation history with them.")
    
    # Helper methods
    @staticmethod
    def _show_navigation_links(state_manager) -> None:
        """Show navigation links in sidebar"""
        app_mode = state_manager.get_app_mode()
        
        if app_mode != "contacts_list":
            if show_navigation_button("🏠 My Contacts", "nav_contacts"):
                state_manager.navigate_to("contacts_list")
                state_manager.set_active_contact(None)
                st.rerun()
        
        if app_mode == "contacts_list" or app_mode == "conversation":
            if show_navigation_button("➕ Add Contact", "nav_add_contact"):
                state_manager.navigate_to("add_contact")
                st.rerun()
    
    @staticmethod
    def _show_contacts_sidebar(state_manager) -> None:
        """Show contacts in sidebar"""
        contacts = state_manager.get_contacts()
        if not contacts:
            st.markdown("*No contacts yet*")
        else:
            for contact_name, contact_data in contacts.items():
                context_icon = CONTEXTS[contact_data['context']]['icon']
                is_active = state_manager.get_active_contact() == contact_name
                
                if st.button(
                    f"{context_icon} {contact_name}",
                    key=f"sidebar_contact_{contact_name}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    state_manager.set_active_contact(contact_name)
                    state_manager.navigate_to("conversation")
                    st.rerun()
    
    @staticmethod
    def _show_mission_reminder() -> None:
        """Show mission reminder in sidebar"""
        st.markdown("### 💙 Our Mission")
        st.markdown("""
        *"When both people are speaking from pain, someone must be the third voice."*
        
        **We help families heal through better conversations.**
        """)
    
    @staticmethod
    def _handle_quick_contact_creation(context_key: str, state_manager, data_manager) -> None:
        """Handle quick contact creation from context buttons"""
        default_names = {
            "romantic": "Partner",
            "coparenting": "Co-parent", 
            "workplace": "Colleague",
            "family": "Family Member",
            "friend": "Friend"
        }
        contact_name = default_names.get(context_key, context_key.title())
        
        if data_manager.save_contact(contact_name, context_key):
            contacts = data_manager.load_contacts_and_history()
            state_manager.set_contacts(contacts)
            state_manager.set_active_contact(contact_name)
            state_manager.navigate_to("conversation")
            st.rerun()
    
    @staticmethod
    def _show_custom_contact_form(state_manager, data_manager, form_type: str) -> None:
        """Show custom contact form"""
        with st.form(f"{form_type}_contact_form"):
            if form_type == "first_time":
                st.markdown("**Or add a custom contact:**")
                name_key = "first_time_new_contact_name_input"
                context_key = "first_time_new_contact_context_select"
                button_text = "Add Custom Contact"
            else:
                name_key = "add_contact_name_input_widget"
                context_key = "add_contact_context_select_widget"
                button_text = "Add Contact"
            
            name = show_form_input(
                "Contact Name" if form_type != "first_time" else "Name",
                name_key,
                placeholder="Sarah, Mom, Dad, Boss..." if form_type != "first_time" else "Sarah, Mom, Dad..."
            )
            
            context = show_selectbox(
                "Relationship Type" if form_type != "first_time" else "Relationship",
                list(CONTEXTS.keys()),
                context_key,
                format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}" + (f" - {CONTEXTS[x]['description']}" if form_type != "first_time" else "")
            )
            
            if st.form_submit_button(button_text, use_container_width=True):
                if name.strip():
                    if data_manager.save_contact(name.strip(), context):
                        contacts = data_manager.load_contacts_and_history()
                        state_manager.set_contacts(contacts)
                        if form_type == "first_time":
                            state_manager.set_active_contact(name.strip())
                            state_manager.navigate_to("conversation")
                        else:
                            display_success(f"Added {name.strip()}! Ready to start healing conversations.")
                            state_manager.navigate_to("contacts_list")
                        st.rerun()
                else:
                    display_error("Contact name cannot be empty.")
    
    @staticmethod
    def _show_welcome_message() -> None:
        """Show welcome message for first-time setup"""
        st.markdown("---")
        st.markdown("### 💙 You're About to Transform Your Relationships")
        st.info("""
        **The Third Voice AI** helps you navigate emotionally charged conversations with wisdom and love.
        
        Whether someone just hurt you, or you're struggling to express yourself without causing pain — 
        we're here to be that calm, healing voice when both people are speaking from pain.
        """)
    
    @staticmethod
    def _show_empty_contacts_state(state_manager) -> None:
        """Show empty state for contacts list"""
        st.info("**No contacts yet.** Add your first contact to get started!")
        if show_navigation_button("➕ Add New Contact", "add_first_contact"):
            state_manager.navigate_to("add_contact")
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
    
    @staticmethod
    def _sort_contacts_by_activity(contacts: Dict) -> list:
        """Sort contacts by most recent activity"""
        sorted_contacts = []
        for name, data in contacts.items():
            last_activity = data["history"][-1]["time"] if data["history"] else data.get("created_at", "")
            sorted_contacts.append((name, data, last_activity))
        
        sorted_contacts.sort(key=lambda x: x[2], reverse=True)
        return sorted_contacts
    
    @staticmethod
    def _display_contact_buttons(sorted_contacts: list, state_manager) -> None:
        """Display contact buttons with preview"""
        for name, data, _ in sorted_contacts:
            last_msg = data["history"][-1] if data["history"] else None
            preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start your first conversation!"
            time_str = last_msg["time"] if last_msg else "New"
            context_icon = CONTEXTS.get(data["context"], {"icon": "💬"})["icon"]
            
            if show_contact_card(name, context_icon, preview, time_str, f"contact_{name}"):
                state_manager.set_active_contact(name)
                state_manager.navigate_to("conversation")
                st.rerun()
    
    @staticmethod
    def _show_conversation_header(state_manager, contact_id: str, active_contact: str, context: str) -> None:
        """Show conversation header with contact name and small edit button"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {CONTEXTS[context]['icon']} {active_contact} - {CONTEXTS[context]['description']}")
        
        with col2:
            if st.button("✏️", key="edit_contact_btn", help="Edit contact", use_container_width=False):
                state_manager.set_edit_contact({
                    "id": contact_id,
                    "name": active_contact,
                    "context": context
                })
                state_manager.navigate_to("edit_contact")
                st.rerun()
    
    @staticmethod
    def _show_conversation_navigation(state_manager) -> None:
        """Show conversation navigation buttons"""
        if show_navigation_button("← Back", "back_btn"):
            state_manager.navigate_to("contacts_list")
            state_manager.set_active_contact(None)
            state_manager.clear_error()
            st.rerun()
    
    @staticmethod
    def _show_relationship_progress(ai_processor, history: list) -> None:
        """Show relationship progress if available"""
        try:
            health_score, status = ai_processor.calculate_relationship_health_score(history)
            with st.expander("📊 **Relationship Healing Progress**", expanded=False):
                col1, col2 = create_two_column_layout()
                with col1:
                    create_metric_card("Relationship Health", f"{health_score}/10")
                with col2:
                    create_metric_card("Total Conversations", len(history))
                st.markdown(f"**Status:** {status}")
        except Exception as e:
            logger.error(f"Error calculating relationship health: {str(e)}")
    
    @staticmethod
    def _show_input_section(state_manager, data_manager, ai_processor, active_contact: str, context: str, history: list, contact_id: str) -> None:
        """Show message input section"""
        logger.debug(f"Rendering input section for {active_contact}, clear flag: {state_manager.should_clear_input()}, input length: {len(state_manager.get_conversation_input())}")
        if state_manager.should_clear_input():
            st.session_state.conversation_input_text = ""
            state_manager.reset_clear_flag()

        st.markdown("#### 💭 Your Input")
        st.markdown("*Share what happened - their message or your response that needs guidance*")
        
        # Message input
        message = st.text_area(
            "What's happening?",
            value=state_manager.get_conversation_input(),
            key="conversation_input_text",
            placeholder="Examples:\n• They said: 'You never listen to me!'\n• I want to tell them: 'I'm frustrated with your attitude'\n• We had a fight about...",
            height=120
        )
        logger.debug(f"Text area rendered with message: {message[:50]}...")
        
        # Action buttons
        col1, col2, col3 = create_three_column_layout()
        with col1:
            if show_navigation_button("✨ Transform with Love", "transform_message"):
                if not message.strip():
                    display_error(ERROR_MESSAGES["empty_message"])
                else:
                    MainUI._process_transform_message(state_manager, data_manager, ai_processor, active_contact, context, history, contact_id, message)
        
        with col2:
            logger.debug(f"Interpret button state: enabled={ENABLE_INTERPRETATION and bool(message.strip())}, text_length={len(message.strip())}")
            if ENABLE_INTERPRETATION and message.strip():
                if show_navigation_button("🔍 Interpret - What do they really mean?", "interpret_btn"):
                    logger.info(f"Interpret button clicked for {active_contact}, message: {message[:50]}...")
                    MainUI._process_interpret_message(state_manager, data_manager, ai_processor, active_contact, context, history, contact_id, message)
            else:
                st.button("🔍 Interpret", disabled=True, help="Enter a message first", key="interpret_btn_disabled", use_container_width=True)
        
        with col3:
            if show_navigation_button("🗑️ Clear", "clear_input_btn"):
                state_manager.set('clear_conversation_input', True)
                state_manager.clear_error()
                st.rerun()
        
        # Display interpretation results if available
        MainUI._show_interpretation_results(state_manager, active_contact)
    
    @staticmethod
    def _process_transform_message(state_manager, data_manager, ai_processor, active_contact: str, context: str, history: list, contact_id: str, message: str) -> None:
        """Process transform message request"""
        logger.debug(f"Processing transform message for contact: {active_contact}, message: {message[:50]}..., context: {context}, history length: {len(history)}")
        try:
            # Validate session state
            debug_info = state_manager.get_debug_info()
            logger.debug(f"Current session state: {debug_info}")

            # Process message with AI
            logger.info(f"Calling ai_processor.process_message for {active_contact}")
            is_incoming = utils.detect_message_type(message) == "translate"
            result = ai_processor.process_message(
                contact_name=active_contact,
                message=message,
                context=context,
                history=history,
                is_incoming=is_incoming
            )
            logger.debug(f"AI processor result: {result}")

            if result.get("success", False):
                logger.info(f"Saving message for contact_id: {contact_id}")
                save_success = data_manager.save_message(
                    contact_id=contact_id,
                    contact_name=active_contact,
                    message_type=result["message_type"],
                    original=message,
                    result=result["response"],
                    emotional_state=result["emotional_state"],
                    healing_score=result["healing_score"],
                    model_used=result["model"],
                    sentiment=result["sentiment"]
                )
                
                if save_success:
                    state_manager.set_last_response(active_contact, result)
                    logger.info(f"Message saved successfully, setting clear input flag for {active_contact}")
                    state_manager.set('clear_conversation_input', True)
                    st.rerun()
                else:
                    logger.error("Failed to save message in data_manager")
                    display_error("Failed to save message. Please try again.")
            else:
                error_msg = result.get("error", "Unknown error in AI processing")
                logger.error(f"AI processor failed: {error_msg}")
                display_error(error_msg)
        except Exception as e:
            logger.exception(f"Error processing message for {active_contact}: {str(e)}")
            display_error("Failed to process message. Please try again.")
    
    @staticmethod
    def _process_interpret_message(state_manager, data_manager, ai_processor, active_contact: str, context: str, history: list, contact_id: str, message: str) -> None:
        """Process interpret message request"""
        logger.debug(f"Processing interpret message for contact: {active_contact}, message: {message[:50]}..., context: {context}, history length: {len(history)}")
        try:
            result = ai_processor.interpret_message(
                contact_name=active_contact,
                message=message,
                context=context,
                history=history
            )
            logger.debug(f"Interpret message result: {result}")
            
            if result["success"]:
                logger.info(f"Saving interpretation for contact_id: {contact_id}")
                state_manager.set_last_interpretation(active_contact, result)
                save_success = data_manager.save_interpretation(
                    contact_id=contact_id,
                    contact_name=active_contact,
                    original_message=message,
                    interpretation=result["interpretation"],
                    interpretation_score=result["interpretation_score"],
                    model_used=result["model"]
                )
                
                if save_success:
                    logger.info(f"Interpretation saved successfully for {active_contact}")
                    state_manager.set('clear_conversation_input', True)
                    st.rerun()
                else:
                    logger.error("Failed to save interpretation in data_manager")
                    display_error("Failed to save interpretation. Please try again.")
            else:
                error_msg = result.get("error", "Unknown error in interpretation")
                logger.error(f"Interpretation failed: {error_msg}")
                display_error(error_msg)
        except Exception as e:
            logger.exception(f"Error interpreting message for {active_contact}: {str(e)}")
            display_error("Failed to interpret message. Please try again.")
    
    @staticmethod
    def _show_interpretation_results(state_manager, active_contact: str) -> None:
        """Show interpretation results if available"""
        last_interpretation = state_manager.get_last_interpretation(active_contact)
        if last_interpretation:
            with st.expander("🔍 **Emotional Analysis - What They Really Mean**", expanded=True):
                st.markdown(last_interpretation["interpretation"])
                
                col1, col2 = create_two_column_layout()
                with col1:
                    score = last_interpretation["interpretation_score"]
                    st.markdown(f"**Healing Score**: {get_healing_score_explanation(score)}")
                
                with col2:
                    if show_copy_button("📋 Copy", "copy_interpretation"):
                        st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
    
    @staticmethod
    def _show_ai_response_section(state_manager, active_contact: str, history: list) -> None:
        """Show AI response section"""
        st.markdown("#### 🤖 The Third Voice Guidance")
        last_response = state_manager.get_last_response(active_contact)
        
        if last_response:
            with st.container():
                st.markdown("**Your AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_response['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                
                col_score, col_model, col_copy = create_three_column_layout()
                with col_score:
                    healing_score = last_response.get("healing_score", 0)
                    st.markdown(f"**Healing Score**: {get_healing_score_explanation(healing_score)}")
                
                with col_model:
                    st.caption(f"🤖 Model: {last_response.get('model', 'Unknown')}")
                
                with col_copy:
                    if show_copy_button("📋", "copy_hint"):
                        st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
                
                if healing_score >= 8:
                    st.markdown("🌟 **High healing potential!** This guidance can really help transform your relationship.")
                
                if last_response.get("cached"):
                    st.info("Response from cache")
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
    
    @staticmethod
    def _show_conversation_history(history: list) -> None:
        """Show conversation history section"""
        st.markdown("#### 📜 Conversation History")
        
        if history:
            st.markdown(f"**Recent Messages** ({len(history)} total healing conversations)")
            
            # Show recent messages in main view
            for msg in reversed(history[-3:]):  # Show last 3 messages
                show_conversation_message(msg, "recent")
            
            # Expandable full history
            if len(history) > 3:
                with st.expander(f"📚 View All {len(history)} Conversations", expanded=False):
                    for msg in reversed(history):
                        show_conversation_message(msg, "full_history")
        else:
            st.info("📝 No conversation history yet. Share what's happening above to get your first Third Voice guidance!")
    
    @staticmethod
    def _show_edit_contact_form(edit_contact: Dict, state_manager, data_manager) -> None:
        """Show edit contact form"""
        with st.form("edit_contact_form"):
            new_name = show_form_input("Contact Name", "edit_contact_name", value=edit_contact['name'])
            new_context = show_selectbox(
                "Relationship Type",
                list(CONTEXTS.keys()),
                "edit_contact_context",
                format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()} - {CONTEXTS[x]['description']}",
                index=list(CONTEXTS.keys()).index(edit_contact['context'])
            )
            
            col1, col2 = create_two_column_layout()
            
            with col1:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    MainUI._handle_contact_update(edit_contact, new_name, new_context, state_manager, data_manager)
            
            with col2:
                if st.form_submit_button("🗑️ Delete Contact", use_container_width=True, type="secondary"):
                    MainUI._handle_contact_deletion(edit_contact, state_manager, data_manager)
    
    @staticmethod
    def _handle_contact_update(edit_contact: Dict, new_name: str, new_context: str, state_manager, data_manager) -> None:
        """Handle contact update"""
        if new_name.strip():
            try:
                if data_manager.update_contact(
                    contact_id=edit_contact['id'],
                    old_name=edit_contact['name'],
                    new_name=new_name.strip(),
                    new_context=new_context
                ):
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    state_manager.set_active_contact(new_name.strip())
                    display_success(f"Updated contact: {new_name.strip()}")
                    state_manager.navigate_to("conversation")
                    state_manager.set_edit_contact(None)
                    st.rerun()
                else:
                    display_error("Failed to update contact")
            except Exception as e:
                logger.error(f"Error updating contact: {str(e)}")
                display_error("Failed to update contact. Please try again.")
        else:
            display_error("Contact name cannot be empty")
    
    @staticmethod
    def _handle_contact_deletion(edit_contact: Dict, state_manager, data_manager) -> None:
        """Handle contact deletion"""
        try:
            if data_manager.delete_contact(edit_contact['id'], edit_contact['name']):
                contacts = data_manager.load_contacts_and_history()
                state_manager.set_contacts(contacts)
                display_success(f"Deleted contact: {edit_contact['name']}")
                state_manager.navigate_to("contacts_list")
                state_manager.set_active_contact(None)
                state_manager.set_edit_contact(None)
                st.rerun()
            else:
                display_error("Failed to delete contact")
        except Exception as e:
            logger.error(f"Error deleting contact: {str(e)}")
            display_error("Failed to delete contact. Please try again.")
