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
from third_voice_ai.utils import utils, show_feedback_widget, display_error, display_success
from third_voice_ai.data_manager import data_manager
from third_voice_ai.state_manager import state_manager
import validators
from passlib.hash import bcrypt
import pandas as pd
import numpy as np
from loguru import logger
from dateutil.parser import parse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logger.add("app.log", rotation="500 MB")

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
    
    # Handle authentication state
    if not state_manager.is_authenticated():
        if state_manager.get_app_mode() == "verification_notice":
            show_verification_notice()
        elif state_manager.get_app_mode() == "signup":
            show_signup_page()
        else:
            show_login_page()
    else:
        show_main_app()

def show_login_page():
    """Display login page matching original design"""
    st.title("🎙️ The Third Voice AI")
    st.subheader("Login to continue your healing journey.")
    
    # Mission statement at top
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **We are that voice** — calm, wise, and healing.
    """)
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            if not validators.email(email):
                display_error("Invalid email format")
                return
            
            if auth_manager.sign_in(email, password):
                state_manager.clear_error()
                st.rerun()
            else:
                display_error(state_manager.get_error() or ERROR_MESSAGES["authentication_failed"])
    
    st.markdown("---")
    st.subheader("New User?")
    if st.button("Create an Account", use_container_width=True):
        state_manager.set_app_mode("signup")
        st.rerun()
    
    # Show mission context
    with st.expander("💙 Our Mission", expanded=False):
        st.markdown("""
        **The Third Voice AI** was born from communication breakdowns that shattered a family. 
        We're turning pain into purpose, helping families heal through better conversations.
        
        Built with love by Predrag Mirkovic, fighting to return to his 6-year-old daughter Samantha 
        after 15 months apart. Every feature serves family healing.
        """)

def show_signup_page():
    """Display signup page matching original design"""
    st.title("🎙️ Join The Third Voice AI")
    st.subheader("Start your journey towards healthier conversations.")
    
    # Mission context
    st.markdown("""
    > *"When both people are speaking from pain, someone must be the third voice."*
    
    **Join thousands rebuilding their most important relationships.**
    """)
    
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password (minimum 6 characters)", type="password", key="signup_password")
        signup_button = st.form_submit_button("Create Account", use_container_width=True)
        
        if signup_button:
            if not validators.email(email):
                display_error("Invalid email format")
                return
            
            if len(password) < 6:
                display_error("Password must be at least 6 characters long.")
                return
            
            if auth_manager.sign_up(email, password):
                display_success(UI_MESSAGES["verification_sent"])
                st.rerun()
            else:
                display_error(state_manager.get_error() or "Sign-up failed")
    
    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Go to Login", use_container_width=True):
        state_manager.set_app_mode("login")
        st.rerun()
    
    # Preview what they'll get
    with st.expander("✨ What you'll get access to", expanded=True):
        st.markdown("""
        **🌟 Transform difficult conversations** - Turn anger into understanding
        
        **💕 Multi-relationship support** - Romantic, family, workplace, co-parenting, friendships
        
        **🎯 Context-aware guidance** - AI understands your specific relationship dynamics
        
        **📊 Healing progress tracking** - See your communication improvement over time
        
        **💾 Conversation history** - Access all your guided conversations anytime
        
        **🚀 Always improving** - Built by a father fighting to heal his own family
        """)

def show_verification_notice():
    """Display verification notice page matching original design"""
    st.title("🎙️ Welcome to The Third Voice AI")
    
    st.success("✅ Account created successfully!")
    
    st.markdown("### 📧 Check Your Email")
    email = state_manager.get("verification_email")
    st.info(f"""
    **Verification email sent to:** `{email}`
    
    **Next steps:**
    1. Check your email inbox (and spam folder)
    2. Click the verification link in the email
    3. Return here and log in
    
    **⏰ The verification email may take a few minutes to arrive.**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📨 Resend Verification Email", use_container_width=True):
            if auth_manager.resend_verification(email):
                display_success("Verification email resent!")
            else:
                display_error("Could not resend email. Please try signing up again if needed.")
    
    with col2:
        if st.button("🔑 Go to Login", use_container_width=True):
            state_manager.clear_verification_notice()
            state_manager.set_app_mode("login")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 💙 Welcome to The Family Healing Revolution")
    st.markdown("""
    **The Third Voice AI** helps families communicate with love, understanding, and healing. 
    You're about to join thousands of people rebuilding their most important relationships.
    
    *"When both people are speaking from pain, someone must be the third voice."*
    """)
    
    # Add helpful tips while they wait
    with st.expander("💡 What to expect after verification", expanded=True):
        st.markdown("""
        **Once you're verified and logged in, you'll be able to:**
        
        - ✨ Transform difficult conversations into healing moments
        - 💕 Get guidance for romantic, family, work, and friendship relationships  
        - 🎯 Receive personalized coaching based on your relationship context
        - 📊 Track your healing progress with our scoring system
        - 💬 Access your conversation history across all your contacts
        
        **Built by a father separated from his daughter, for every family seeking healing.**
        """)

def show_main_app():
    """Display main application interface with sidebar and proper navigation"""
    # Sidebar for navigation and contact management
    with st.sidebar:
        st.markdown("### 🎙️ The Third Voice AI")
        user = state_manager.get_user()
        st.write(f"**{user.email}**")
        
        if st.button("🚪 Logout", use_container_width=True):
            if auth_manager.sign_out():
                state_manager.clear_authentication()
                st.rerun()
        
        st.markdown("---")
        st.header("Navigation")
        
        # Quick navigation links
        app_mode = state_manager.get_app_mode()
        
        if app_mode != "contacts_list":
            if st.button("🏠 My Contacts", use_container_width=True):
                state_manager.navigate_to("contacts_list")
                state_manager.set_active_contact(None)
                st.rerun()
        
        if app_mode == "contacts_list" or app_mode == "conversation":
            if st.button("➕ Add Contact", use_container_width=True):
                state_manager.navigate_to("add_contact")
                st.rerun()
        
        st.markdown("---")
        st.header("Contacts")
        
        contacts = state_manager.get_contacts()
        if not contacts:
            st.markdown("*No contacts yet*")
        else:
            # Display contact list in sidebar
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
        
        st.markdown("---")
        
        # Mission reminder
        st.markdown("### 💙 Our Mission")
        st.markdown("""
        *"When both people are speaking from pain, someone must be the third voice."*
        
        **We help families heal through better conversations.**
        """)
    
    # Main content area
    app_mode = state_manager.get_app_mode()
    
    if app_mode == "first_time_setup":
        show_first_time_setup()
    elif app_mode == "add_contact":
        show_add_contact()
    elif app_mode == "conversation":
        show_conversation()
    elif app_mode == "contacts_list":
        show_contacts_list()
    elif app_mode == "edit_contact":
        show_edit_contact()
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

def show_first_time_setup():
    """Display first-time setup page matching original design"""
    st.markdown("### 🎙️ Welcome to The Third Voice")
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
                # Create default contact names
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
    
    st.markdown("---")
    
    # Custom contact form
    with st.form("add_custom_contact_first_time"):
        st.markdown("**Or add a custom contact:**")
        name = st.text_input("Name", placeholder="Sarah, Mom, Dad...", key="first_time_new_contact_name_input")
        context = st.selectbox(
            "Relationship", 
            list(CONTEXTS.keys()), 
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()}", 
            key="first_time_new_contact_context_select"
        )
        
        if st.form_submit_button("Add Custom Contact", use_container_width=True):
            if name.strip():
                if data_manager.save_contact(name.strip(), context):
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    state_manager.set_active_contact(name.strip())
                    state_manager.navigate_to("conversation")
                    st.rerun()
            else:
                display_error("Contact name cannot be empty.")
    
    # Welcome message and feedback
    st.markdown("---")
    st.markdown("### 💙 You're About to Transform Your Relationships")
    st.info("""
    **The Third Voice AI** helps you navigate emotionally charged conversations with wisdom and love.
    
    Whether someone just hurt you, or you're struggling to express yourself without causing pain — 
    we're here to be that calm, healing voice when both people are speaking from pain.
    """)

def show_add_contact():
    """Display add contact page matching original design"""
    st.markdown("### ➕ Add New Contact")
    
    if st.button("← Back to Contacts", key="back_to_contacts", use_container_width=True):
        state_manager.navigate_to("contacts_list")
        state_manager.clear_error()
        st.rerun()
    
    st.markdown("**Tell us about this relationship so we can provide better guidance:**")
    
    with st.form("add_contact_form"):
        name = st.text_input("Contact Name", placeholder="Sarah, Mom, Dad, Boss...", key="add_contact_name_input_widget")
        context = st.selectbox(
            "Relationship Type", 
            list(CONTEXTS.keys()),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()} - {CONTEXTS[x]['description']}",
            key="add_contact_context_select_widget"
        )
        
        if st.form_submit_button("Add Contact", use_container_width=True):
            if name.strip():
                if data_manager.save_contact(name.strip(), context):
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    display_success(f"Added {name.strip()}! Ready to start healing conversations.")
                    state_manager.navigate_to("contacts_list")
                    st.rerun()
            else:
                display_error("Contact name cannot be empty.")

def show_contacts_list():
    """Display contacts list matching original design"""
    st.markdown("### 🎙️ The Third Voice - Your Contacts")
    
    contacts = state_manager.get_contacts()
    
    if not contacts:
        st.info("**No contacts yet.** Add your first contact to get started!")
        if st.button("➕ Add New Contact", use_container_width=True):
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
        return
    
    # Sort contacts by most recent activity
    sorted_contacts = []
    for name, data in contacts.items():
        last_activity = data["history"][-1]["time"] if data["history"] else data.get("created_at", "")
        sorted_contacts.append((name, data, last_activity))
    
    sorted_contacts.sort(key=lambda x: x[2], reverse=True)
    
    st.markdown(f"**{len(sorted_contacts)} contact{'s' if len(sorted_contacts) != 1 else ''}** • Tap to continue conversation")
    
    # Display contacts as buttons with preview
    for name, data, _ in sorted_contacts:
        last_msg = data["history"][-1] if data["history"] else None
        preview = f"{last_msg['original'][:40]}..." if last_msg and last_msg['original'] else "Start your first conversation!"
        time_str = last_msg["time"] if last_msg else "New"
        context_icon = CONTEXTS.get(data["context"], {"icon": "💬"})["icon"]
        
        if st.button(
            f"{context_icon} **{name}** • {time_str}\n_{preview}_",
            key=f"contact_{name}",
            use_container_width=True
        ):
            state_manager.set_active_contact(name)
            state_manager.navigate_to("conversation")
            st.rerun()
    
    st.markdown("---")
    if st.button("➕ Add New Contact", use_container_width=True):
        state_manager.navigate_to("add_contact")
        st.rerun()
    
    # Analytics section if enabled
    if ENABLE_ANALYTICS:
        try:
            stats = data_manager.get_user_stats()
            st.subheader("Your Stats")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Contacts", stats.get('contact_count', 0))
            with col2:
                st.metric("Total Messages", stats.get('message_count', 0))
            with col3:
                st.metric("Avg Healing Score", f"{stats.get('avg_healing_score', 0):.1f}")
        except Exception as e:
            logger.error(f"Error loading analytics: {str(e)}")
            st.warning("Analytics temporarily unavailable")

def show_conversation():
    """Display conversation interface matching original design"""
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
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {active_contact} - {CONTEXTS[context]['description']}")
    
    # Navigation buttons
    back_col, edit_col, _ = st.columns([2, 2, 6])
    with back_col:
        if st.button("← Back", key="back_btn", use_container_width=True):
            state_manager.navigate_to("contacts_list")
            state_manager.set_active_contact(None)
            state_manager.clear_error()
            st.rerun()
    
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            state_manager.set_edit_contact({
                "id": contact_id,
                "name": active_contact,
                "context": context
            })
            state_manager.navigate_to("edit_contact")
            st.rerun()
    
    # Display relationship progress if available
    if ENABLE_ANALYTICS and history:
        try:
            health_score, status = ai_processor.calculate_relationship_health_score(history)
            with st.expander("📊 **Relationship Healing Progress**", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Relationship Health", f"{health_score}/10")
                with col2:
                    st.metric("Total Conversations", len(history))
                st.markdown(f"**Status:** {status}")
        except Exception as e:
            logger.error(f"Error calculating relationship health: {str(e)}")
    
    st.markdown("---")
    
    # Input section
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
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message", use_container_width=True):
            if not message.strip():
                display_error(ERROR_MESSAGES["empty_message"])
            else:
                try:
                    result = ai_processor.process_message(
                        contact_name=active_contact,
                        message=message,
                        context=context,
                        history=history
                    )
                    
                    if result["success"]:
                        state_manager.set_last_response(active_contact, result)
                        data_manager.save_message(
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
                        state_manager.clear_conversation_input()
                        st.rerun()
                    else:
                        display_error(result["error"])
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    display_error("Failed to process message. Please try again.")
    
    with col2:
        if ENABLE_INTERPRETATION and message.strip():
            if st.button("🔍 Interpret - What do they really mean?", key="interpret_btn", use_container_width=True):
                try:
                    result = ai_processor.interpret_message(
                        contact_name=active_contact,
                        message=message,
                        context=context,
                        history=history
                    )
                    
                    if result["success"]:
                        state_manager.set_last_interpretation(active_contact, result)
                        data_manager.save_interpretation(
                            contact_id=contact_id,
                            contact_name=active_contact,
                            original_message=message,
                            interpretation=result["interpretation"],
                            interpretation_score=result["interpretation_score"],
                            model_used=result["model"]
                        )
                        st.rerun()
                    else:
                        display_error(result["error"])
                except Exception as e:
                    logger.error(f"Error interpreting message: {str(e)}")
                    display_error("Failed to interpret message. Please try again.")
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first", use_container_width=True)
    
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            state_manager.clear_conversation_input()
            state_manager.clear_error()
            st.rerun()
    
    # Display interpretation results if available
    last_interpretation = state_manager.get_last_interpretation(active_contact)
    if last_interpretation:
        with st.expander("🔍 **Emotional Analysis - What They Really Mean**", expanded=True):
            st.markdown(last_interpretation["interpretation"])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                score = last_interpretation["interpretation_score"]
                if score >= 8:
                    st.success(f"✨ Deep Insight Score: {score}/10 - Very revealing analysis")
                elif score >= 6:
                    st.info(f"💡 Insight Score: {score}/10 - Good understanding")
                else:
                    st.warning(f"🔍 Insight Score: {score}/10 - Basic analysis")
            
            with col2:
                if st.button("📋 Copy", key="copy_interpretation"):
                    st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
    
    st.markdown("---")
    
    # AI Response section
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
            
            col_score, col_model, col_copy = st.columns([2, 2, 1])
            with col_score:
                healing_score = last_response.get("healing_score", 0)
                if healing_score >= 8:
                    st.success(f"✨ Healing Score: {healing_score}/10")
                elif healing_score >= 6:
                    st.info(f"💡 Healing Score: {healing_score}/10")
                else:
                    st.warning(f"🔧 Healing Score: {healing_score}/10")
            
            with col_model:
                st.caption(f"🤖 Model: {last_response.get('model', 'Unknown')}")
            
            with col_copy:
                if st.button("📋", help="Click text area above and Ctrl+A to select all", key="copy_hint"):
                    st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
            
            if healing_score >= 8:
                st.balloons()
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
    
    st.markdown("---")
    
    # Conversation History
    st.markdown("#### 📜 Conversation History")
    
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total healing conversations)")
        
        # Show recent messages in main view
        for msg in reversed(history[-3:]):  # Show last 3 messages
            with st.container():
                col_time, col_score = st.columns([3, 1])
                with col_time:
                    st.markdown(f"**{msg['time']}** • {msg['type'].title()}")
                with col_score:
                    score = msg.get('healing_score', 0)
                    score_color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                    st.markdown(f"{score_color} {score}/10")
                
                st.markdown("**Your Message:**")
                st.info(msg['original'])
                
                if msg.get('result'):
                    st.markdown("**Third Voice Guidance:**")
                    st.text_area(
                        "Historical AI Guidance",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg.get('id', hash(msg['original']))}",
                        disabled=True,
                        label_visibility="hidden"
                    )
                
                st.markdown("---")
        
        # Expandable full history
        if len(history) > 3:
            with st.expander(f"📚 View All {len(history)} Conversations", expanded=False):
                for msg in reversed(history):
                    st.markdown(f"""
                    **{msg['time']}** | **{msg['type'].title()}** | Score: {msg.get('healing_score', 0)}/10
                    """)
                    
                    with st.container():
                        st.markdown("**Your Message:**")
                        st.info(msg['original'])
                    
                    if msg.get('result'):
                        with st.container():
                            st.markdown("**Third Voice Guidance:**")
                            st.text_area(
                                "Full History AI Guidance",
                                value=msg['result'],
                                height=100,
                                key=f"full_history_response_{msg.get('id', hash(msg['original'] + str(msg['time'])))}",
                                disabled=True,
                                label_visibility="hidden"
                            )
                            st.caption(f"🤖 Model: {msg.get('model', 'Unknown')}")
                    
                    st.markdown("---")
    else:
        st.info("📝 No conversation history yet. Share what's happening above to get your first Third Voice guidance!")

def show_edit_contact():
    """Display edit contact page"""
    edit_contact = state_manager.get_edit_contact()
    if not edit_contact:
        state_manager.navigate_to("contacts_list")
        st.rerun()
        return
    
    st.markdown(f"### ✏️ Edit Contact: {edit_contact['name']}")
    
    if st.button("← Back", key="back_to_conversation", use_container_width=True):
        state_manager.navigate_to("conversation")
        state_manager.set_edit_contact(None)
        st.rerun()
    
    with st.form("edit_contact_form"):
        new_name = st.text_input("Contact Name", value=edit_contact['name'])
        new_context = st.selectbox(
            "Relationship Type",
            list(CONTEXTS.keys()),
            index=list(CONTEXTS.keys()).index(edit_contact['context']),
            format_func=lambda x: f"{CONTEXTS[x]['icon']} {x.title()} - {CONTEXTS[x]['description']}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                if new_name.strip():
                    try:
                        if data_manager.update_contact(
                            contact_id=edit_contact['id'],
                            old_name=edit_contact['name'],
                            new_name=new_name.strip(),
                            new_context=new_context
                        ):
                            # Update session state
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
        
        with col2:
            if st.form_submit_button("🗑️ Delete Contact", use_container_width=True, type="secondary"):
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
    
    # Warning about deletion
    st.warning("⚠️ Deleting a contact will permanently remove all conversation history with them.")


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
