"""
App Controller Module for The Third Voice AI
Main application controller that orchestrates all components
Enhanced with better logout functionality and session persistence
"""

import streamlit as st
import traceback
from .components import UIComponents
from .pages import OnboardingFlow, Dashboard, AdminDashboard


class AuthenticationUI:
    """Handles authentication UI and logic"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
    
    def run(self):
        """Render authentication UI and handle login"""
        # Check if already authenticated
        if self.auth_manager.is_authenticated():
            return True
        
        # Handle Google OAuth callback
        user = self.auth_manager.handle_google_callback()
        if user:
            return True
        
        # Display authentication UI
        st.title("The Third Voice AI - Login")
        st.write("Sign in to access your personalized dashboard")
        
        # Google Sign-In
        self.auth_manager.sign_in_with_google()
        
        # Email/Password Sign-In
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")
            if submit:
                success, message = self.auth_manager.sign_in(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        # Sign-Up
        with st.form("signup_form"):
            signup_email = st.text_input("Email for Sign Up")
            signup_password = st.text_input("Password for Sign Up", type="password")
            signup_submit = st.form_submit_button("Sign Up")
            if signup_submit:
                success, message = self.auth_manager.sign_up(signup_email, signup_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        return False


class ThirdVoiceApp:
    """Main application controller"""
    
    def __init__(self, db_manager, ai_engine, auth_manager):
        self.db = db_manager
        self.ai_engine = ai_engine
        self.auth_manager = auth_manager
        self.auth_ui = AuthenticationUI(self.auth_manager)
        self.onboarding = OnboardingFlow(self.db, self.ai_engine)
        self.dashboard = Dashboard(self.db, self.ai_engine)
        self.admin_dashboard = AdminDashboard(self.db)
    
    def run(self):
        """Main application entry point"""
        UIComponents.load_custom_css()
        try:
            query_params = st.query_params
            if query_params.get('admin') == 'true':
                if not self.auth_ui.run():
                    return
                user_id = self.auth_manager.get_current_user_id()
                if user_id:
                    self.admin_dashboard.run(user_id, self.auth_manager)
                return
        except:
            try:
                query_params = st.experimental_get_query_params()
                if 'admin' in query_params and query_params['admin'][0] == 'true':
                    if not self.auth_ui.run():
                        return
                    user_id = self.auth_manager.get_current_user_id()
                    if user_id:
                        self.admin_dashboard.run(user_id, self.auth_manager)
                    return
            except:
                pass
        
        if not self.auth_ui.run():
            return
        
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            st.error("Authentication error. Please refresh the page.")
            return
        
        if not st.session_state.get('onboarding_completed', False):
            contacts = self.db.get_user_contacts(user_id)
            if not contacts:
                if self.onboarding.run(user_id, self.auth_manager):
                    st.rerun()
                return
            else:
                st.session_state.onboarding_completed = True
        
        self.dashboard.run(user_id, self.auth_manager)


def run_app():
    """Application entry point function"""
    try:
        from ..data.database import DatabaseManager
        from ..core.ai_engine import AIEngine
        from ..auth.auth_manager import AuthManager
        db = DatabaseManager()
        ai_engine = AIEngine()
        auth_manager = AuthManager(db)
        app = ThirdVoiceApp(db, ai_engine, auth_manager)
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.code(traceback.format_exc())