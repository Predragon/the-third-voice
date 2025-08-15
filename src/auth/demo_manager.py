"""
Demo Manager for The Third Voice AI
Handles demo account login, usage tracking, and session management
"""

import streamlit as st
import datetime
from src.data.database import db

DEMO_EMAIL = "demo@thethirdvoice.ai"
DEMO_PASSWORD = "demo1234"

class DemoManager:
    """Manage demo account login and usage tracking"""

    @staticmethod
    def sign_in():
        """Sign in as demo user (pseudo-user in session)"""
        class DemoUser:
            def __init__(self, email):
                self.id = "demo_user"
                self.email = email

        st.session_state.user = DemoUser(DEMO_EMAIL)

        # Track demo usage in Supabase
        try:
            ip_address = st.request.remote_addr if hasattr(st, "request") else None
            login_time = datetime.datetime.utcnow().isoformat()
            db.supabase.table("demo_usage").insert({
                "user_email": DEMO_EMAIL,
                "login_time": login_time,
                "ip_address": ip_address
            }).execute()
        except Exception as e:
            st.warning(f"Could not log demo usage: {e}")

        st.info("Signed in as Demo User (messages are not saved)")

    @staticmethod
    def is_demo():
        """Check if current user is demo"""
        return getattr(st.session_state, "user", None) and st.session_state.user.email == DEMO_EMAIL
