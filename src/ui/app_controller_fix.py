"""
App Controller Module for The Third Voice AI
Main application controller that orchestrates all components
Enhanced with better logout functionality and session persistence
"""

import streamlit as st
import traceback
from .components import UIComponents
from .pages import AuthenticationUI, OnboardingFlow, Dashboard


class ThirdVoiceApp:
    """Main application controller"""
    
    def __init__(self, db_manager, ai_engine, auth_manager):
        self.db = db_manager
        self.ai_engine = ai_engine
        self.auth_manager = auth_manager
        self.auth_ui = AuthenticationUI(self.auth_manager)
        self.onboarding = OnboardingFlow(self.db, self.ai_engine)
        self.dashboard = Dashboard(self.db, self.ai_engine)
    
    def run(self):
        """Main application entry point"""
        
        # Load custom CSS for mobile optimization
        UIComponents.load_custom_css()
        
        # Authentication check
        if not self.auth_ui.run():
            return
        
        # Get current user
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            st.error("Authentication error. Please refresh the page.")
            return
        
        # Check if user needs onboarding
        if not st.session_state.get('onboarding_completed', False):
            contacts = self.db.get_user_contacts(user_id)
            if not contacts:
                # First time user - run onboarding
                if self.onboarding.run(user_id, self.auth_manager):
                    st.rerun()
                return
            else:
                # Has contacts but hasn't seen onboarding completion
                st.session_state.onboarding_completed = True
        
        # Run main dashboard
        self.dashboard.run(user_id, self.auth_manager)


def run_app():
    """Application entry point function"""
    try:
        # Import here to avoid circular imports
        from ..data.database import DatabaseManager
        from ..core.ai_engine import AIEngine
        from ..auth.auth_manager import AuthManager
        
        # Initialize components
        db = DatabaseManager()
        ai_engine = AIEngine()
        auth_manager = AuthManager(db)
        
        # Create and run app
        app = ThirdVoiceApp(db, ai_engine, auth_manager)
        app.run()
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        # Log the full traceback for debugging
        st.code(traceback.format_exc())