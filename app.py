import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
from third_voice_ai.config import (
    APP_NAME, APP_ICON, PAGE_CONFIG, CONTEXTS, UI_MESSAGES,
    ENABLE_ANALYTICS, ENABLE_FEEDBACK, ENABLE_INTERPRETATION, ERROR_MESSAGES
)
from third_voice_ai.auth_manager import auth_manager
from third_voice_ai.ai_processor import ai_processor
from third_voice_ai.prompts import prompt_manager
from third_voice_ai.data_manager import data_manager
from third_voice_ai.state_manager import state_manager
from third_voice_ai.ui import AuthUI, MainUI
from third_voice_ai.ui.components import show_feedback_widget, display_error, display_success
import validators
from passlib.hash import bcrypt
import pandas as pd
import numpy as np
from third_voice_ai import get_logger
from dateutil.parser import parse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logger = get_logger("app")

# Set Streamlit page configuration
st.set_page_config(
    page_title="The Third Voice AI",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def main():
    """Main application logic"""
    logger.info("Starting The Third Voice AI application")
    
    # Initialize session state
    state_manager.init_session_state()
    
    # Try to restore authentication session on every app load
    if not state_manager.is_authenticated():
        session_restored = auth_manager.restore_session()
        if session_restored:
            logger.info("Session successfully restored from Supabase")
            # Force a rerun to update the UI with the restored session
            st.rerun()
    
    # Handle authentication state
    if not state_manager.is_authenticated():
        handle_authentication()
    else:
        show_main_app()

def handle_authentication():
    """Handle authentication flow"""
    app_mode = state_manager.get_app_mode()
    
    if app_mode == "verification_notice":
        AuthUI.show_verification_notice(auth_manager, state_manager)
    elif app_mode == "signup":
        AuthUI.show_signup_page(auth_manager, state_manager)
    else:
        AuthUI.show_login_page(auth_manager, state_manager)

def show_main_app():
    """Display main application interface with sidebar and proper navigation"""
    # Show sidebar
    MainUI.show_sidebar(state_manager, auth_manager)
    
    # Main content area
    app_mode = state_manager.get_app_mode()
    
    # Route to appropriate page based on app mode
    if app_mode == "first_time_setup":
        MainUI.show_first_time_setup(state_manager, data_manager)
    elif app_mode == "add_contact":
        MainUI.show_add_contact_page(state_manager, data_manager)
    elif app_mode == "conversation":
        MainUI.show_conversation_interface(state_manager, data_manager, ai_processor)
    elif app_mode == "contacts_list":
        MainUI.show_contacts_list(state_manager, data_manager)
    elif app_mode == "edit_contact":
        MainUI.show_edit_contact_page(state_manager, data_manager)
    else:
        # Default to contacts list
        state_manager.navigate_to("contacts_list")
        st.rerun()
    
    # Display error if present
    if state_manager.get_error():
        display_error(state_manager.get_error())
        state_manager.clear_error()
    
    # Single feedback widget for main app - only show if enabled
    if ENABLE_FEEDBACK:
        show_feedback_widget(context="main_app")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page.")
        if st.button("🔄 Refresh Page"):
            st.rerun()
    
    # Single feedback widget at app level - removed from individual functions
    # This ensures only one feedback widget appears per page load
