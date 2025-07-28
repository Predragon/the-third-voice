import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
from config import (
    APP_NAME, APP_ICON, PAGE_CONFIG, CONTEXTS, UI_MESSAGES,
    ENABLE_ANALYTICS, ENABLE_FEEDBACK, ENABLE_INTERPRETATION, ERROR_MESSAGES
)
from auth_manager import auth_manager
from third_voice_ai.ai_processor import AIProcessor
#from ai_processor import ai_processor
from prompts import prompt_manager
from utils import utils, show_feedback_widget, display_error, display_success
from data_manager import data_manager
from state_manager import state_manager
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
st.set_page_config(**PAGE_CONFIG)

def main():
    """Main application logic"""
    logger.info("Starting The Third Voice AI application")
    
    # Initialize session state
    state_manager.init_session_state()
    
    # Handle authentication state
    if not state_manager.is_authenticated():
        if state_manager.get_app_mode() == "verification_notice":
            show_verification_notice()
        else:
            show_auth_page()
    else:
        show_main_app()

def show_auth_page():
    """Display authentication page (login/signup)"""
    st.title(f"{APP_ICON} {APP_NAME}")
    st.markdown(UI_MESSAGES["welcome_first_time"])
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")
            
            if submit:
                if not validators.email(email):
                    display_error("Invalid email format")
                    return
                
                is_valid, error_msg = utils.validate_password(password)
                if not is_valid:
                    display_error(error_msg)
                    return
                
                if auth_manager.sign_in(email, password):
                    state_manager.clear_error()
                    st.rerun()  # Updated from experimental_rerun
                else:
                    display_error(state_manager.get_error() or ERROR_MESSAGES["authentication_failed"])
    
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if not validators.email(email):
                    display_error("Invalid email format")
                    return
                
                is_valid, error_msg = utils.validate_password(password)
                if not is_valid:
                    display_error(error_msg)
                    return
                
                if auth_manager.sign_up(email, password):
                    display_success(UI_MESSAGES["verification_sent"])
                    st.rerun()  # Updated from experimental_rerun
                else:
                    display_error(state_manager.get_error() or "Sign-up failed")

def show_verification_notice():
    """Display verification notice page"""
    st.title(f"{APP_ICON} {APP_NAME}")
    email = state_manager.get("verification_email")
    st.info(f"Verification email sent to {email}. Please check your inbox and spam folder.")
    
    if st.button("Resend Verification Email"):
        if auth_manager.resend_verification(email):
            display_success("Verification email resent!")
        else:
            display_error("Failed to resend verification email")
    
    if st.button("Back to Login"):
        state_manager.clear_verification_notice()
        state_manager.set_app_mode("login")
        st.rerun()  # Updated from experimental_rerun

def show_main_app():
    """Display main application interface"""
    st.title(f"{APP_ICON} {APP_NAME}")
    st.markdown(UI_MESSAGES["healing_mission"])
    
    # Sidebar for navigation and contact management
    with st.sidebar:
        st.header("Navigation")
        user = state_manager.get_user()
        st.write(f"Welcome, {user.email}")
        
        if st.button("Sign Out"):
            if auth_manager.sign_out():
                state_manager.clear_authentication()
                st.rerun()  # Updated from experimental_rerun
        
        st.header("Contacts")
        if state_manager.get_app_mode() == "first_time_setup":
            st.markdown(UI_MESSAGES["no_contacts"])
        
        if st.button("Add Contact"):
            state_manager.navigate_to("add_contact")
        
        contacts = state_manager.get_contacts()
        for contact_name, contact_data in contacts.items():
            if st.button(f"{CONTEXTS[contact_data['context']]['icon']} {contact_name}"):
                state_manager.set_active_contact(contact_name)
                state_manager.navigate_to("conversation")
    
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
    
    # Display error if present
    if state_manager.get_error():
        display_error(state_manager.get_error())
        state_manager.clear_error()
    
    # Feedback widget
    if ENABLE_FEEDBACK:
        show_feedback_widget(context="main_app")

def show_first_time_setup():
    """Display first-time setup page"""
    st.header("Welcome to Your Healing Journey")
    st.markdown(UI_MESSAGES["welcome_first_time"])
    show_add_contact()

def show_add_contact():
    """Display add/edit contact page"""
    st.header("Add New Contact")
    
    with st.form("add_contact_form"):
        name = st.text_input("Contact Name", value=state_manager.get("add_contact_name_input"))
        context = st.selectbox("Relationship Type", options=list(CONTEXTS.keys()),
                              format_func=lambda x: f"{CONTEXTS[x]['icon']} {CONTEXTS[x]['description']}",
                              index=list(CONTEXTS.keys()).index(state_manager.get("add_contact_context_select")))
        submit = st.form_submit_button("Add Contact")
        
        if submit:
            if not utils.validate_contact_name(name):
                display_error("Contact name cannot be empty")
                return
            
            if data_manager.save_contact(name, context):
                state_manager.update({
                    "add_contact_name_input": "",
                    "add_contact_context_select": list(CONTEXTS.keys())[0]
                })
                contacts = data_manager.load_contacts_and_history()
                state_manager.set_contacts(contacts)
                state_manager.navigate_to("contacts_list")
                display_success(f"Contact {name} added successfully!")
                st.rerun()  # Updated from experimental_rerun

def show_contacts_list():
    """Display contacts list with basic stats"""
    st.header("Your Contacts")
    contacts = state_manager.get_contacts()
    
    if not contacts:
        st.markdown(UI_MESSAGES["no_contacts"])
        return
    
    # Create a DataFrame for contact stats
    contact_stats = []
    for name, data in contacts.items():
        health_score, status = ai_processor.calculate_relationship_health_score(data["history"])
        contact_stats.append({
            "Name": name,
            "Context": CONTEXTS[data["context"]]["description"],
            "Messages": len(data["history"]),
            "Health Score": health_score,
            "Status": status
        })
    
    df = pd.DataFrame(contact_stats)
    st.dataframe(df, use_container_width=True)
    
    if ENABLE_ANALYTICS:
        stats = data_manager.get_user_stats()
        st.subheader("Your Stats")
        st.write(f"Total Contacts: {stats.get('contact_count', 0)}")
        st.write(f"Total Messages: {stats.get('message_count', 0)}")
        st.write(f"Average Healing Score: {stats.get('avg_healing_score', 0)}")

def show_conversation():
    """Display conversation interface for active contact"""
    active_contact = state_manager.get_active_contact()
    if not active_contact:
        display_error(ERROR_MESSAGES["contact_not_found"])
        state_manager.navigate_to("contacts_list")
        return
    
    contact_data = state_manager.get_contact_data(active_contact)
    st.header(f"{CONTEXTS[contact_data['context']]['icon']} {active_contact}")
    
    # Display conversation history
    history = contact_data["history"]
    if history:
        st.subheader("Recent Messages")
        for msg in history[-3:]:  # Show last 3 messages
            st.markdown(f"**{msg['time']}** ({msg['type']}): {utils.format_conversation_preview(msg['original'])}")
            if msg["result"]:
                st.markdown(f"> {utils.get_healing_score_color(msg['healing_score'])} {msg['result']}")
    
    # Message input and processing
    with st.form("conversation_form"):
        message = st.text_area("Your Message", value=state_manager.get_conversation_input(),
                              placeholder=UI_MESSAGES["guidance_placeholder"])
        col1, col2 = st.columns(2)
        with col1:
            transform_btn = st.form_submit_button("Transform")
        with col2:
            if ENABLE_INTERPRETATION:
                interpret_btn = st.form_submit_button("Interpret")
        
        if transform_btn:
            if not message.strip():
                display_error(ERROR_MESSAGES["empty_message"])
                return
            
            result = ai_processor.process_message(
                contact_name=active_contact,
                message=message,
                context=contact_data["context"],
                history=history
            )
            
            if result["success"]:
                state_manager.set_last_response(active_contact, result)
                data_manager.save_message(
                    contact_id=contact_data["id"],
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
                st.rerun()  # Updated from experimental_rerun
            else:
                display_error(result["error"])
        
        if ENABLE_INTERPRETATION and interpret_btn:
            if not message.strip():
                display_error(ERROR_MESSAGES["empty_message"])
                return
            
            result = ai_processor.interpret_message(
                contact_name=active_contact,
                message=message,
                context=contact_data["context"],
                history=history
            )
            
            if result["success"]:
                state_manager.set_last_interpretation(active_contact, result)
                data_manager.save_interpretation(
                    contact_id=contact_data["id"],
                    contact_name=active_contact,
                    original_message=message,
                    interpretation=result["interpretation"],
                    interpretation_score=result["interpretation_score"],
                    model_used=result["model"]
                )
                state_manager.clear_conversation_input()
                st.rerun()  # Updated from experimental_rerun
            else:
                display_error(result["error"])
    
    # Display last response or interpretation
    last_response = state_manager.get_last_response(active_contact)
    last_interpretation = state_manager.get_last_interpretation(active_contact)
    
    if last_response:
        st.subheader("AI Guidance")
        st.markdown(f"{utils.get_healing_score_color(last_response['healing_score'])} {last_response['response']}")
        st.markdown(utils.get_healing_score_message(last_response['healing_score']))
        if last_response["cached"]:
            st.info("Response from cache")
    
    if last_interpretation:
        st.subheader("Interpretation")
        st.markdown(last_interpretation["interpretation"])
        st.markdown(f"Insight Score: {last_interpretation['interpretation_score']}/10")

if __name__ == "__main__":
    main()
