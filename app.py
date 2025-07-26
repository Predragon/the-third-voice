"""
app.py - The Third Voice AI Main Application

The main entry point for our family healing application.
Built with love from detention, for every family seeking healing.

"When both people are speaking from pain, someone must be the third voice."
"""

import streamlit as st
from datetime import datetime

# Import our core modules
from ui_components import (
    render_app_header,
    render_mission_sidebar,
    render_login_form,
    render_signup_form,
    render_verification_notice,
    render_first_time_setup,
    render_contacts_list,
    render_add_contact_form,
    render_edit_contact_form,
    render_conversation_header,
    render_relationship_progress,
    render_conversation_input,
    render_interpretation_result,
    render_ai_response_section,
    render_conversation_history,
    render_error_display,
    render_feedback_widget
)
from data_backend import (
    restore_user_session,
    load_contacts_and_history
)

# === APP CONFIGURATION ===
st.set_page_config(
    page_title="The Third Voice AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile experience
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Mobile-friendly spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Better button styling */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        margin: 0.25rem 0;
    }
    
    /* Improved text areas */
    .stTextArea > div > div > textarea {
        border-radius: 10px;
    }
    
    /* Better expander styling */
    .streamlit-expanderHeader {
        font-weight: bold;
    }
    
    /* Contact card styling */
    .stButton > button[kind="secondary"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        color: #495057;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #e9ecef;
        border-color: #adb5bd;
    }
</style>
""", unsafe_allow_html=True)

# === SESSION STATE INITIALIZATION ===
def initialize_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.app_mode = "login"  # login, signup, verification_notice, contacts_list, conversation_view, add_contact_view, edit_contact_view
    
    if "contacts" not in st.session_state:
        st.session_state.contacts = {}
    
    if "active_contact" not in st.session_state:
        st.session_state.active_contact = None
    
    if "conversation_input_text" not in st.session_state:
        st.session_state.conversation_input_text = ""
    
    if "clear_conversation_input" not in st.session_state:
        st.session_state.clear_conversation_input = False
    
    if "last_error_message" not in st.session_state:
        st.session_state.last_error_message = None
    
    if "edit_contact" not in st.session_state:
        st.session_state.edit_contact = None
    
    if "show_verification_notice" not in st.session_state:
        st.session_state.show_verification_notice = False
    
    if "verification_email" not in st.session_state:
        st.session_state.verification_email = ""

# === MAIN APPLICATION LOGIC ===
def main():
    """Main application logic"""
    
    # Initialize session state
    initialize_session_state()
    
    # Try to restore user session on app reload
    if not st.session_state.authenticated:
        if restore_user_session():
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    
    # Load user data if authenticated
    if st.session_state.authenticated and not st.session_state.contacts:
        st.session_state.contacts = load_contacts_and_history()
    
    # Render sidebar (always visible when authenticated)
    if st.session_state.authenticated:
        render_mission_sidebar()
    
    # Main content routing
    if st.session_state.app_mode == "login":
        render_login_form()
    
    elif st.session_state.app_mode == "signup":
        render_signup_form()
    
    elif st.session_state.app_mode == "verification_notice":
        render_verification_notice()
    
    elif st.session_state.authenticated:
        
        if st.session_state.app_mode == "contacts_list":
            if not st.session_state.contacts:
                render_first_time_setup()
            else:
                render_contacts_list()
        
        elif st.session_state.app_mode == "conversation_view":
            render_conversation_view()
        
        elif st.session_state.app_mode == "add_contact_view":
            render_add_contact_form()
        
        elif st.session_state.app_mode == "edit_contact_view":
            render_edit_contact_form()
        
        else:
            # Fallback to contacts list
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    
    else:
        # User not authenticated, redirect to login
        st.session_state.app_mode = "login"
        st.rerun()

def render_conversation_view():
    """Render the main conversation interface"""
    
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name)
    
    if not contact_data:
        st.error(f"Contact '{contact_name}' not found.")
        st.session_state.app_mode = "contacts_list"
        st.session_state.active_contact = None
        st.rerun()
        return
    
    context = contact_data["context"]
    contact_id = contact_data["id"]
    history = contact_data["history"]
    
    # Render conversation interface
    render_conversation_header(contact_name, context, contact_id)
    
    # Show any error messages
    render_error_display()
    
    # Relationship progress (collapsible)
    render_relationship_progress(contact_name, history)
    
    # Show interpretation results if available
    render_interpretation_result(contact_name)
    
    # Main input interface
    render_conversation_input(contact_name, context, history)
    
    # AI response section
    render_ai_response_section(contact_name)
    
    # Conversation history
    render_conversation_history(history)
    
    # Feedback widget
    render_feedback_widget(f"conversation_{contact_name}")

# === ERROR HANDLING ===
def handle_uncaught_exception(e):
    """Handle any uncaught exceptions gracefully"""
    st.error("An unexpected error occurred. Please refresh the page or contact support.")
    st.exception(e)
    
    # Reset to safe state
    st.session_state.app_mode = "contacts_list" if st.session_state.authenticated else "login"
    st.session_state.active_contact = None
    st.session_state.last_error_message = None

# === APPLICATION ENTRY POINT ===
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        handle_uncaught_exception(e)
