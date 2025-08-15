"""
App Controller Module for The Third Voice AI
Main application controller that orchestrates all components
Enhanced with demo account support, AI chat, and session persistence
"""

import streamlit as st
import traceback
from .components import UIComponents
from .pages import AuthenticationUI, OnboardingFlow, Dashboard, AdminDashboard
from ..auth.demo_manager import DemoManager


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

        # Load custom CSS
        UIComponents.load_custom_css()

        # Admin mode support
        try:
            query_params = st.query_params
            if query_params.get('admin') == ['true']:
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

        # --- Demo login button ---
        if st.button("Use Demo Account"):
            DemoManager.sign_in(self.db)  # Pass DatabaseManager instance here

        # Demo warning
        if DemoManager.is_demo():
            st.warning("⚠️ This is a demo account. Messages are not saved, but usage is tracked.")

        # Authentication check
        if not DemoManager.is_demo() and not self.auth_ui.run():
            return

        # Get current user
        user = getattr(st.session_state, "user", None)
        user_id = user.id if user else self.auth_manager.get_current_user_id()
        if not user_id:
            st.error("Authentication error. Please refresh the page.")
            return

        # Onboarding
        if not st.session_state.get('onboarding_completed', False):
            contacts = self.db.get_user_contacts(user_id)
            if not contacts:
                if self.onboarding.run(user_id, self.auth_manager):
                    st.rerun()
                return
            else:
                st.session_state.onboarding_completed = True

        # --- Main AI Chat Section ---
        st.subheader("AI Chat")
        user_email = user.email if user else self.auth_manager.get_current_user_email()
        st.session_state.setdefault('demo_messages', [])

        user_input = st.text_area("Your message:")

        if st.button("Send"):
            if user_input.strip():
                # Use AIEngine instance instead of separate function
                response = self.ai_engine.generate_response(user_email, user_input)

                # Display response
                st.text_area("AI Response:", value=response, height=200)

                if DemoManager.is_demo():
                    # Store messages in session only
                    DemoManager.add_message(user_input, response)
                else:
                    # Save for real users
                    from ..data.database import save_message
                    save_message(user_email, user_input)

        # --- Display past demo messages if demo ---
        if DemoManager.is_demo() and st.session_state['demo_messages']:
            st.subheader("Demo Chat History (Session Only)")
            for msg in st.session_state['demo_messages']:
                st.markdown(f"**You:** {msg['input']}")
                st.markdown(f"**AI:** {msg['response']}")
                st.markdown("---")


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
