"""
main_app.py - The Third Voice AI Main Application

This should be your main Streamlit app file that orchestrates everything.
"""

import streamlit as st
from datetime import datetime, timezone

# Import your modules
from data_backend import (
    init_supabase_connection,
    load_contacts_and_history,
    get_current_user_id
)
from ui_components import (
    render_mission_sidebar,
    render_login_form,
    render_signup_form,
    render_verification_notice,
    render_first_time_setup,
    render_contacts_list,
    render_add_contact_form,
    render_edit_contact_form,
    render_conversation_view,
    render_error_display
)


def init_session_state():
    """Initialize session state with default values"""
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
        'add_contact_context_select': "romantic",
        'last_error_message': None,
        'show_verification_notice': False,
        'verification_email': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def restore_session():
    """Restore user session on app reload"""
    try:
        supabase = init_supabase_connection()
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


def render_conversation_view():
    """Main conversation view - this was missing from ui_components"""
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    
    # Import these from ui_components
    from ui_components import (
        render_conversation_header,
        render_relationship_progress,
        render_conversation_input,
        render_interpretation_result,
        render_ai_response_section,
        render_conversation_history,
        render_feedback_widget
    )
    
    # Render conversation interface
    render_conversation_header(contact_name, context, contact_id)
    render_relationship_progress(contact_name, history)
    
    st.markdown("---")
    
    render_conversation_input(contact_name, context, history)
    render_error_display()
    render_interpretation_result(contact_name)
    
    st.markdown("---")
    
    render_ai_response_section(contact_name)
    
    st.markdown("---")
    
    render_conversation_history(history)
    render_feedback_widget(f"conversation_{contact_name}")


def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize everything
    init_session_state()
    restore_session()
    
    # Render sidebar
    render_mission_sidebar()
    
    # Route to appropriate view based on authentication and app mode
    if st.session_state.authenticated:
        if st.session_state.app_mode == "first_time_setup":
            render_first_time_setup()
        elif st.session_state.app_mode == "contacts_list":
            render_contacts_list()
        elif st.session_state.app_mode == "conversation_view":
            render_conversation_view()
        elif st.session_state.app_mode == "edit_contact_view":
            render_edit_contact_form()
        elif st.session_state.app_mode == "add_contact_view":
            render_add_contact_form()
        else:
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    else:
        if st.session_state.app_mode == "signup":
            render_signup_form()
        elif st.session_state.app_mode == "verification_notice":
            render_verification_notice()
        else:
            render_login_form()


if __name__ == "__main__":
    main()
