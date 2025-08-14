"""
App Controller Module for The Third Voice AI
Main application controller that orchestrates all components
Enhanced with streamlit-supabase-auth for reliable authentication
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
    
    def _handle_authentication(self):
        """Handle authentication flow using streamlit-supabase-auth
        
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        # Check if user is already authenticated
        if self.auth_manager.is_authenticated():
            # Show logout button in sidebar
            self.auth_manager.render_logout_button(location="sidebar")
            return True
        
        # User is not authenticated - show login form
        self._show_landing_page()
        
        # Render login form and check for successful authentication
        session = self.auth_manager.render_login_form()
        
        if session:
            # User just logged in successfully
            st.success("✅ Welcome! Redirecting to your dashboard...")
            st.rerun()  # Refresh to show authenticated state
            return True
        
        # User not authenticated yet
        return False
    
    def _show_landing_page(self):
        """Show landing page for non-authenticated users"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>🌟 The Third Voice AI</h1>
            <h3>Transform Your Communication, Heal Your Relationships</h3>
            <p style='font-size: 1.1em; color: #666; max-width: 600px; margin: 0 auto;'>
                Navigate difficult conversations with AI-powered guidance. Get personalized responses 
                that promote healing and understanding in your most important relationships.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create three columns for features
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **💬 Smart Responses**  
            AI-crafted messages that promote healing and understanding
            """)
        
        with col2:
            st.markdown("""
            **🎯 Context-Aware**  
            Tailored advice for romantic, family, workplace, and co-parenting situations
            """)
        
        with col3:
            st.markdown("""
            **🔒 Private & Secure**  
            Your conversations stay confidential with enterprise-grade security
            """)
        
        st.markdown("---")
        st.markdown("### 👇 Sign in to get started")


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
