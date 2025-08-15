"""
Demo Manager for The Third Voice AI
Handles demo account login, session-based chat, and usage tracking
"""

import streamlit as st
import datetime
from ..data.database import db  # Your DatabaseManager instance

DEMO_EMAIL = "demo@thethirdvoice.ai"
DEMO_PASSWORD = "demo1234"


class DemoManager:
    """Manage demo account login and session messages"""

    @staticmethod
    def sign_in():
        """Sign in as demo user and initialize session"""
        class DemoUser:
            def __init__(self, email):
                self.id = "demo_user"
                self.email = email

        st.session_state.user = DemoUser(DEMO_EMAIL)
        st.session_state.setdefault('demo_messages', [])

        # Track demo usage in Supabase
        try:
            ip_address = None
            if hasattr(st, "request") and getattr(st.request, "remote_addr", None):
                ip_address = st.request.remote_addr
            login_time = datetime.datetime.utcnow().isoformat()
            db.supabase.table("demo_usage").insert({
                "user_email": DEMO_EMAIL,
                "login_time": login_time,
                "ip_address": ip_address
            }).execute()
        except Exception as e:
            st.warning(f"Could not log demo usage: {e}")

        st.info("Signed in as Demo User (messages are not saved to database)")

    @staticmethod
    def is_demo():
        """Return True if current user is demo"""
        return getattr(st.session_state, "user", None) and st.session_state.user.email == DEMO_EMAIL

    @staticmethod
    def add_message(input_text, response_text):
        """Store a message in session only"""
        if DemoManager.is_demo():
            st.session_state.setdefault('demo_messages', [])
            st.session_state['demo_messages'].append({
                "input": input_text,
                "response": response_text
            })

    @staticmethod
    def get_messages():
        """Retrieve session messages for demo user"""
        if DemoManager.is_demo():
            return st.session_state.get('demo_messages', [])
        return []
