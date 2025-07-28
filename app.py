# app.py - The Third Voice AI (Complete Modular Application)
# Helping families heal through better communication
# Built with love by Predrag Mirkovic for Samantha and all families seeking healing

import streamlit as st
from datetime import datetime
import json

# Import our modular components
from config import (
    APP_NAME, APP_ICON, VERSION, MISSION_STATEMENT, 
    CONTEXTS, PAGE_CONFIG, UI_MESSAGES, ERROR_MESSAGES
)
from state_manager import state_manager
from auth.py import AuthManager
from data_manager import DataManager
from ai_processor import AIProcessor
from utils import (
    format_timestamp, validate_contact_name, sanitize_input,
    get_relationship_health_status, calculate_healing_trend,
    show_feedback_widget, display_error, display_success
)
from prompts import prompt_manager, get_context_tips

# Initialize components
auth_manager = AuthManager()
data_manager = DataManager()
ai_processor = AIProcessor()

def init_app():
    """Initialize the application"""
    st.set_page_config(**PAGE_CONFIG)
    
    # Restore user session if available
    auth_manager.restore_session()

def render_sidebar():
    """Render the sidebar with navigation and debug info"""
    with st.sidebar:
        st.markdown(f"### {APP_ICON} {APP_NAME}")
        st.caption(f"Version {VERSION}")
        
        if state_manager.is_authenticated():
            user = state_manager.get_user()
            st.write(f"**{user.email}**")
            
            # Quick navigation
            current_mode = state_manager.get_app_mode()
            if current_mode != "contacts_list":
                if st.button("🏠 My Contacts", use_container_width=True):
                    state_manager.set_app_mode("contacts_list")
                    state_manager.set_active_contact(None)
                    st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                auth_manager.sign_out()
        
        st.markdown("---")
        
        # Mission statement
        st.markdown("### 💙 Our Mission")
        st.markdown(UI_MESSAGES['healing_mission'])
        
        # Tips for current context
        active_contact = state_manager.get_active_contact()
        if active_contact:
            contacts = state_manager.get_contacts()
            if active_contact in contacts:
                context = contacts[active_contact]['context']
                tips = get_context_tips(context)
                
                with st.expander(f"💡 {context.title()} Tips", expanded=False):
                    for tip in tips[:3]:  # Show top 3 tips
                        st.markdown(f"• {tip}")
        
        # Debug info (collapsed by default)
        if st.checkbox("🔧 Debug Info"):
            debug_info = {
                "Mode": state_manager.get_app_mode(),
                "Authenticated": state_manager.is_authenticated(),
                "Active Contact": state_manager.get_active_contact(),
                "Contacts Count": len(state_manager.get_contacts()),
                "Has Error": bool(state_manager.get_error())
            }
            
            st.code(json.dumps(debug_info, indent=2), language="json")

def render_verification_notice():
    """Render email verification notice page"""
    st.title(f"{APP_ICON} Welcome to {APP_NAME}")
    
    st.success("✅ Account created successfully!")
    
    verification_email = state_manager.get('verification_email')
    
    st.markdown("### 📧 Check Your Email")
    st.info(f"""
    **Verification email sent to:** `{verification_email}`
    
    **Next steps:**
    1. Check your email inbox (and spam folder)
    2. Click the verification link in the email
    3. Return here and log in
    
    **⏰ The verification email may take a few minutes to arrive.**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📨 Resend Verification Email", use_container_width=True):
            if auth_manager.resend_verification(verification_email):
                display_success("Verification email resent!")
            else:
                st.warning("Could not resend email. Please try signing up again if needed.")
    
    with col2:
        if st.button("🔑 Go to Login", use_container_width=True):
            state_manager.set_app_mode("login")
            state_manager.clear_key('show_verification_notice')
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 💙 Welcome to The Family Healing Revolution")
    st.markdown(UI_MESSAGES['welcome_new_user'])

def render_login_page():
    """Render login page"""
    st.title(f"{APP_ICON} {APP_NAME}")
    st.subheader("Login to continue your healing journey.")
    
    st.markdown(f"> *{MISSION_STATEMENT}*")
    st.markdown("**We are that voice** — calm, wise, and healing.")
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            if auth_manager.sign_in(email, password):
                # Load user data
                contacts = data_manager.load_contacts_and_history()
                state_manager.set_contacts(contacts)
                
                if contacts:
                    state_manager.set_app_mode("contacts_list")
                else:
                    state_manager.set_app_mode("first_time_setup")
                
                display_success(f"Welcome back, {email}!")
                st.rerun()
    
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account", use_container_width=True):
        state_manager.set_app_mode("signup")
        st.rerun()
    
    # Show mission context
    with st.expander("💙 Our Mission", expanded=False):
        st.markdown(UI_MESSAGES['mission_story'])

def render_signup_page():
    """Render signup page"""
    st.title(f"{APP_ICON} Join {APP_NAME}")
    st.subheader("Start your journey towards healthier conversations.")
    
    st.markdown(f"> *{MISSION_STATEMENT}*")
    st.markdown("**Join thousands rebuilding their most important relationships.**")
    
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password (minimum 6 characters)", type="password", key="signup_password")
        signup_button = st.form_submit_button("Create Account", use_container_width=True)
        
        if signup_button:
            if len(password) < 6:
                display_error("Password must be at least 6 characters long.")
            else:
                if auth_manager.sign_up(email, password):
                    state_manager.set('verification_email', email)
                    state_manager.set_app_mode("verification_notice")
                    st.rerun()
    
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login", use_container_width=True):
        state_manager.set_app_mode("login")
        st.rerun()
    
    # Preview features
    with st.expander("✨ What you'll get access to", expanded=True):
        st.markdown(UI_MESSAGES['feature_preview'])

def render_first_time_setup():
    """Render first-time user setup"""
    st.markdown(f"### {APP_ICON} Welcome to {APP_NAME}")
    st.markdown("**Choose a relationship type to get started, or add a custom contact:**")
    
    # Quick context buttons
    cols = st.columns(2)
    contexts_items = list(CONTEXTS.items())
    
    for i, (context_key, context_info) in enumerate(contexts_items):
        with cols[i % 2]:
            if st.button(
                f"{context_info['icon']} {context_key.title()}\n{context_info['description']}",
                key=f"context_{context_key}",
                use_container_width=True
            ):
                default_name = context_info['default_name']
                
                if data_manager.save_contact(default_name, context_key):
                    # Reload contacts
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    state_manager.set_active_contact(default_name)
                    state_manager.set_app_mode("conversation_view")
                    st.rerun()
    
    st.markdown("---")
    
    # Custom contact form
    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name")
        context = st.selectbox(
            "Relationship", 
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}",
            key="first_time_new_contact_context"
        )
        
        if st.form_submit_button("Add Custom Contact", use_container_width=True):
            name = sanitize_input(name)
            if validate_contact_name(name):
                if data_manager.save_contact(name, context):
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    state_manager.set_active_contact(name)
                    state_manager.set_app_mode("conversation_view")
                    st.rerun()
            else:
                display_error("Contact name cannot be empty.")
    
    # Welcome message
    st.markdown("---")
    st.markdown("### 💙 You're About to Transform Your Relationships")
    st.info(UI_MESSAGES['first_time_welcome'])
    
    # Feedback widget
    show_feedback_widget("first_time_setup")

def render_contacts_list():
    """Render contacts list view"""
    st.markdown(f"### {APP_ICON} {APP_NAME} - Your Contacts")
    
    contacts = state_manager.get_contacts()
    
    if not contacts:
        st.info("**No contacts yet.** Add your first contact to get started!")
        if st.button("➕ Add New Contact", use_container_width=True):
            state_manager.set_app_mode("add_contact_view")
            st.rerun()
        
        # Show helpful context
        st.markdown("---")
        st.markdown("### 💡 How The Third Voice Works")
        st.markdown(UI_MESSAGES['how_it_works'])
        return
    
    # Sort contacts by recent activity
    sorted_contacts = sorted(
        contacts.items(),
        key=lambda x: x[1]["history"][-1]["time"] if x[1]["history"] else x[1]["created_at"],
        reverse=True
    )
    
    st.markdown(f"**{len(sorted_contacts)} contact{'s' if len(sorted_contacts) != 1 else ''}** • Tap to continue conversation")
    
    # Display contacts
    for name, data in sorted_contacts:
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start your first conversation!"
        time_str = format_timestamp(last_msg["time"]) if last_msg else "New"
        context_icon = CONTEXTS.get(data["context"], {"icon": "💬"})["icon"]
        
        # Add health indicator
        health_score, _ = get_relationship_health_status(data["history"])
        health_indicator = "🟢" if health_score >= 7 else "🟡" if health_score >= 5 else "🔴" if health_score > 0 else "⚪"
        
        if st.button(
            f"{context_icon} **{name}** {health_indicator} • {time_str}\n_{preview}_",
            key=f"contact_{name}",
            use_container_width=True
        ):
            state_manager.set_active_contact(name)
            state_manager.set_app_mode("conversation_view")
            state_manager.clear_error()
            st.rerun()
    
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        state_manager.set_app_mode("add_contact_view")
        st.rerun()
    
    # Feedback widget
    show_feedback_widget("contacts_list")

def render_add_contact_view():
    """Render add contact view"""
    st.markdown("### ➕ Add New Contact")
    
    if st.button("← Back to Contacts", use_container_width=True):
        state_manager.set_app_mode("contacts_list")
        st.rerun()
    
    st.markdown("**Tell us about this relationship so we can provide better guidance:**")
    
    with st.form("add_contact_form"):
        name = st.text_input("Contact Name", placeholder="Sarah, Mom, Dad, Boss...")
        context = st.selectbox(
            "Relationship Type", 
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()} - {CONTEXTS[x]['description']}"
        )
        
        if st.form_submit_button("Add Contact", use_container_width=True):
            name = sanitize_input(name)
            if validate_contact_name(name):
                if data_manager.save_contact(name, context):
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    display_success(f"Added {name}! Ready to start healing conversations.")
                    state_manager.set_app_mode("contacts_list")
                    st.rerun()
            else:
                display_error("Contact name cannot be empty.")

def render_edit_contact_view():
    """Render edit contact view"""
    edit_contact = state_manager.get('edit_contact')
    if not edit_contact:
        state_manager.set_app_mode("contacts_list")
        st.rerun()
        return
    
    st.markdown(f"### ✏️ Edit Contact: {edit_contact['name']}")
    
    if st.button("← Back", use_container_width=True):
        state_manager.set_app_mode("conversation_view")
        state_manager.clear_key('edit_contact')
        st.rerun()
    
    with st.form("edit_contact_form"):
        name = st.text_input("Name", value=edit_contact["name"])
        
        context_options = list(CONTEXTS.keys())
        initial_index = context_options.index(edit_contact["context"]) if edit_contact["context"] in context_options else 0
        context = st.selectbox(
            "Relationship", 
            context_options,
            index=initial_index,
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                name = sanitize_input(name)
                if validate_contact_name(name):
                    if data_manager.save_contact(name, context, edit_contact["id"]):
                        # Update active contact if needed
                        if state_manager.get_active_contact() == edit_contact["name"]:
                            state_manager.set_active_contact(name)
                        
                        contacts = data_manager.load_contacts_and_history()
                        state_manager.set_contacts(contacts)
                        display_success(f"Updated {name}")
                        state_manager.set_app_mode("conversation_view")
                        state_manager.clear_key('edit_contact')
                        st.rerun()
                else:
                    display_error("Contact name cannot be empty.")
        
        with col2:
            if st.form_submit_button("🗑️ Delete Contact"):
                if data_manager.delete_contact(edit_contact["id"]):
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    display_success(f"Deleted contact: {edit_contact['name']}")
                    state_manager.set_app_mode("contacts_list")
                    state_manager.set_active_contact(None)
                    state_manager.clear_key('edit_contact')
                    st.rerun()

def render_conversation_view():
    """Render main conversation interface"""
    active_contact = state_manager.get_active_contact()
    if not active_contact:
        state_manager.set_app_mode("contacts_list")
        st.rerun()
        return
    
    contacts = state_manager.get_contacts()
    contact_data = contacts.get(active_contact, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {active_contact} - {CONTEXTS[context]['description']}")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        if st.button("← Back", use_container_width=True):
            state_manager.set_app_mode("contacts_list")
            state_manager.set_active_contact(None)
            state_manager.clear_error()
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit", use_container_width=True):
            state_manager.set('edit_contact', {
                "id": contact_id,
                "name": active_contact,
                "context": context
            })
            state_manager.set_app_mode("edit_contact_view")
            st.rerun()
    
    # Relationship progress section
    if history:
        health_score, status = get_relationship_health_status(history)
        trend = calculate_healing_trend(history)
        
        with st.expander("📊 **Relationship Healing Progress**", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Relationship Health", f"{health_score}/10", help="Based on recent healing scores")
            with col2:
                st.metric("Total Conversations", len(history))
            
            st.markdown(f"**Status:** {status}")
            
            if trend:
                trend_color = "🟢" if "improving" in trend.lower() else "🟡" if "stable" in trend.lower() else "🔴"
                st.markdown(f"**Trend:** {trend_color} {trend}")
    
    st.markdown("---")
    
