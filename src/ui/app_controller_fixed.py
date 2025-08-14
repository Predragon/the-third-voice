"""
App Controller Module for The Third Voice AI
Main application controller that orchestrates all components
FIXED: Authentication flow to work with True Supabase-Centric approach
Never trust session state for authentication decisions
"""

import streamlit as st
import traceback
from .components import UIComponents
from .pages import AuthenticationUI, OnboardingFlow, Dashboard, AdminDashboard


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
        
        # Load custom CSS for mobile optimization
        UIComponents.load_custom_css()
        
        # Check for admin mode (add ?admin=true to URL)
        try:
            query_params = st.query_params
            if query_params.get('admin') == 'true':
                if not self._handle_authentication():
                    return
                user_id = self.auth_manager.get_current_user_id()
                if user_id:
                    self.admin_dashboard.run(user_id, self.auth_manager)
                return
        except:
            # Fallback for older Streamlit versions
            try:
                query_params = st.experimental_get_query_params()
                if 'admin' in query_params and query_params['admin'][0] == 'true':
                    if not self._handle_authentication():
                        return
                    user_id = self.auth_manager.get_current_user_id()
                    if user_id:
                        self.admin_dashboard.run(user_id, self.auth_manager)
                    return
            except:
                pass
        
        # Main authentication and app flow
        if not self._handle_authentication():
            return
        
        # Get current user (always from Supabase, never from session state)
        user_id = self.auth_manager.get_current_user_id()
        if not user_id:
            st.error("Authentication error. Please refresh the page.")
            return
        
        # Check if user needs onboarding
        if not self._user_completed_onboarding(user_id):
            contacts = self.db.get_user_contacts(user_id)
            if not contacts:
                # First time user - run onboarding
                if self.onboarding.run(user_id, self.auth_manager):
                    st.rerun()
                return
            else:
                # Has contacts but hasn't seen onboarding completion message
                # Mark as completed to avoid repeated onboarding
                st.session_state.onboarding_completed = True
        
        # Run main dashboard
        self.dashboard.run(user_id, self.auth_manager)
    
    def _handle_authentication(self):
        """Handle authentication flow - TRUE SUPABASE-CENTRIC VERSION
        
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        # CRITICAL: Always check Supabase first, never trust session state
        if self.auth_manager.is_authenticated():
            # User is authenticated according to Supabase
            # Show logout button in sidebar for authenticated users
            self.auth_manager.render_logout_button(location="sidebar")
            return True
        
        # User is not authenticated in Supabase
        # Run the full authentication UI (Google OAuth + email/password)
        authenticated = self.auth_ui.run()
        
        if authenticated:
            # User successfully authenticated through AuthenticationUI
            st.success("✅ Welcome! Loading your dashboard...")
            # Give a moment for Supabase session to fully establish
            st.rerun()
            return True
        
        # User not authenticated yet - AuthenticationUI is handling the display
        return False
    
    def _user_completed_onboarding(self, user_id: str) -> bool:
        """Check if user has completed onboarding
        
        Don't rely on session state for this check - use database state
        """
        # Check if user has any contacts (indicates onboarding completed)
        contacts = self.db.get_user_contacts(user_id)
        
        # If they have contacts, they've completed onboarding
        if contacts:
            # Cache the result in session state for UI performance
            st.session_state.onboarding_completed = True
            return True
        
        # Check session state as a cache only (not source of truth)
        if st.session_state.get('onboarding_completed', False):
            return True
        
        return False
    
    def _show_landing_page(self):
        """Show landing page for non-authenticated users - NOT USED ANYMORE
        
        This method is now replaced by AuthenticationUI.run() which handles
        the entire authentication flow including landing page content.
        """
        pass  # Keeping for backward compatibility but not used


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
        # Show more user-friendly error in production
        if st.secrets.get("environment", "development") == "production":
            st.info("We're experiencing technical difficulties. Please try refreshing the page.")
        else:
            # Show full traceback in development
            st.code(traceback.format_exc())