# app.py - The Third Voice AI Application
# Main entry point for The Third Voice AI Streamlit app

import streamlit as st
from loguru import logger
from third_voice_ai.ai_processor import AIProcessor
from third_voice_ai.state_manager import StateManager
from third_voice_ai.ui.auth_ui import AuthUI
from third_voice_ai.ui.main_ui import MainUI
from third_voice_ai.auth_manager import auth_manager
from third_voice_ai.data_manager import data_manager
from third_voice_ai.config import PAGE_CONFIG

# Initialize components
state_manager = StateManager()
auth_ui = AuthUI()
main_ui = MainUI()
ai_processor = AIProcessor()

def main():
    """Main application function"""
    logger.info("Starting The Third Voice AI application")
    st.set_page_config(**PAGE_CONFIG)  # Ensure sidebar is collapsed on every load
    state_manager.init_session_state()
    
    if not state_manager.is_authenticated():
        logger.info("User not authenticated, checking for session restoration")
        session_restored = auth_manager.restore_session()
        if session_restored:
            logger.info("Session successfully restored from Supabase")
            st.set_page_config(**PAGE_CONFIG)  # Re-apply to ensure collapsed sidebar
            st.rerun()
        else:
            logger.info("No session to restore, proceeding to authentication")
            auth_ui.show_auth_page(auth_manager, state_manager)
    else:
        logger.info(f"User authenticated, app_mode: {state_manager.get_app_mode()}")
        if state_manager.get_app_mode() == "first_time_setup":
            logger.debug("Rendering first_time_setup page")
            main_ui.show_first_time_setup(state_manager, data_manager)
        elif state_manager.get_app_mode() == "add_contact":
            logger.debug("Rendering add_contact page")
            main_ui.show_add_contact_page(state_manager, data_manager)
        elif state_manager.get_app_mode() == "recent_contacts":
            logger.debug("Rendering recent_contacts page")
            main_ui.show_recent_contacts(state_manager, data_manager)
        elif state_manager.get_app_mode() == "contacts_list":
            logger.debug("Redirecting from contacts_list to recent_contacts")
            state_manager.set_app_mode("recent_contacts")
            st.rerun()
        elif state_manager.get_app_mode() == "conversation":
            logger.debug("Rendering conversation page")
            main_ui.show_conversation_interface(state_manager, data_manager, ai_processor)
        elif state_manager.get_app_mode() == "edit_contact":
            logger.debug("Rendering edit_contact page")
            main_ui.show_edit_contact_page(state_manager, data_manager)
        else:
            logger.warning(f"Unknown app_mode: {state_manager.get_app_mode()}, defaulting to recent_contacts")
            state_manager.set_app_mode("recent_contacts")
            st.rerun()

if __name__ == "__main__":
    main()
