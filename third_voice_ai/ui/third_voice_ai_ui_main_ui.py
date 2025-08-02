import streamlit as st
from typing import Dict, Any, Optional
from .components import (
    display_error, display_success, show_navigation_button, show_form_input,
    show_selectbox, show_contact_card, show_conversation_message, show_healing_score_display,
    show_copy_button, create_two_column_layout, create_three_column_layout, create_metric_card
)
from ..config import CONTEXTS, ENABLE_ANALYTICS, ENABLE_INTERPRETATION, ERROR_MESSAGES
from ..prompts import get_healing_score_explanation
from ..utils import utils
from ..data_manager import DataManager
from loguru import logger

class MainUI:
    def __init__(self, config, auth_manager, state_manager, data_manager: DataManager):
        self.config = config
        self.auth_manager = auth_manager
        self.state_manager = state_manager
        self.data_manager = data_manager

    def initialize_ui(self):
        st.set_page_config(page_title="The Third Voice AI", layout="wide")

    def show_auth_page(self):
        with st.form("auth_form"):
            email = show_form_input("Email", "login_email")
            password = show_form_input("Password", "login_password", "password")
            if show_navigation_button("Login", "login_btn"):
                if self.auth_manager.login(email, password):
                    self.state_manager.set('authenticated', True)
                    st.rerun()
                else:
                    display_error("Login failed. Check your credentials.")
            if show_navigation_button("Sign Up", "signup_btn"):
                self.state_manager.set('app_mode', 'signup')
                st.rerun()

    def show_main_interface(self):
        st.title("The Third Voice AI")
        col1, col2 = st.columns([1, 3])
        with col1:
            self.show_sidebar()
        with col2:
            self._show_input_section()

    def show_sidebar(self):
        with st.sidebar:
            st.markdown("### 🎙️ The Third Voice AI")
            user = self.state_manager.get_user()
            st.write(f"**{user.email if user else 'Guest'}**")
            if show_navigation_button("🚪 Logout", "logout_btn"):
                if self.auth_manager.sign_out():
                    self.state_manager.set('authenticated', False)
                    st.rerun()
                else:
                    display_error("Logout failed.")
            st.markdown("---")
            st.header("Contacts")
            contacts = self.state_manager.get_contacts()
            if show_navigation_button("Add Contact", "add_contact_btn"):
                name = show_form_input("Contact Name", "sidebar_contact_name")
                context = show_selectbox("Context", list(CONTEXTS.keys()), "sidebar_context")
                if show_navigation_button("Save", "save_contact_btn") and name:
                    contact_data = self.data_manager.save_contact(name, context)
                    if contact_data and "id" in contact_data:
                        contacts[name] = contact_data
                        self.state_manager.set_contacts(contacts)
                        display_success(f"Added {name}")
                    else:
                        display_error("Failed to add contact.")
            st.write(f"Total Contacts: {len(contacts)}")

    def _show_input_section(self):
        active_contact = self.state_manager.get_active_contact() or "Co-parent"
        self.state_manager.set_active_contact(active_contact)
        message = st.text_area("Message", height=200, key="message_input")
        message_length = len(message) if message else 0
        self.state_manager.set('conversation_input_length', message_length)

        col1, col2 = create_two_column_layout()
        with col1:
            if show_navigation_button("Transform", "transform_btn"):
                self._process_transform_message(active_contact, message)
        with col2:
            interpret_enabled = ENABLE_INTERPRETATION and bool(message.strip()) and active_contact in self.state_manager.get_contacts()
            if show_navigation_button("Interpret", "interpret_btn", disabled=not interpret_enabled):
                self._process_interpret_message(active_contact, message)

        if self.state_manager.get_error():
            display_error(self.state_manager.get_error())
            self.state_manager.clear_error()

    def _process_transform_message(self, active_contact: str, message: str):
        if not message.strip():
            return
        contact_data = self.state_manager.get_contact_data(active_contact)
        if not contact_data or "id" not in contact_data:
            self.state_manager.set_error("Contact not found. Please add the contact first.")
            return
        contact_id = contact_data["id"]
        result = self.data_manager.ai_processor.process_message(active_contact, message, "family")
        if result.get("success"):
            save_success = self.data_manager.save_message(
                contact_id=contact_id, contact_name=active_contact, message_type="coach",
                original=message, result=result["response"], emotional_state=result["emotional_state"],
                healing_score=result["healing_score"], model_used=result["model"], sentiment=result["sentiment"]
            )
            if save_success:
                self.state_manager.set_last_response(active_contact, result)
                self.state_manager.set('clear_conversation_input', True)
                st.rerun()
            else:
                self.state_manager.set_error("Failed to save message.")
        else:
            self.state_manager.set_error(result.get("error", "Failed to process message."))

    def _process_interpret_message(self, active_contact: str, message: str):
        if not message.strip():
            return
        contact_data = self.state_manager.get_contact_data(active_contact)
        if not contact_data or "id" not in contact_data:
            self.state_manager.set_error("Contact not found. Please add the contact first.")
            return
        contact_id = contact_data["id"]
        result = self.data_manager.ai_processor.interpret_message(active_contact, message, "family")
        if result.get("success"):
            save_success = self.data_manager.save_interpretation(
                contact_id=contact_id, contact_name=active_contact, original_message=message,
                interpretation=result["interpretation"], interpretation_score=result["interpretation_score"], model_used=result["model"]
            )
            if save_success:
                self.state_manager.set_last_interpretation(active_contact, result)
                self.state_manager.set('clear_conversation_input', True)
                st.rerun()
            else:
                self.state_manager.set_error("Failed to save interpretation.")
        else:
            self.state_manager.set_error(result.get("error", "Failed to interpret message."))