# third_voice_ai/ui/auth_ui.py

import streamlit as st
import validators

from typing import Optional

from .components import display_error, display_success, show_form_input, show_navigation_button

from ..config import UI_MESSAGES, ERROR_MESSAGES

class AuthUI:
    """Authentication UI components and handlers"""

    @staticmethod
    def show_login_page(auth_manager, state_manager) -> None:
        """
        Display login page with consistent styling
        """
        st.title("🎙️ The Third Voice AI")
        st.subheader("Login to continue your healing journey.")

        # Mission statement at top
        st.markdown("""
        > *"When both people are speaking from pain, someone must be the third voice."*
        **We are that voice** — calm, wise, and healing.
        """)

        with st.form("login_form"):
            email = show_form_input("Email", "login_email")
            password = show_form_input("Password", "login_password", input_type="password")
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
        if show_navigation_button("Create an Account", "create_account_btn"):
            state_manager.set_app_mode("signup")
            st.rerun()

        # Show mission context
        AuthUI._show_mission_context()

    @staticmethod
    def show_signup_page(auth_manager, state_manager) -> None:
        """
        Display signup page with consistent styling
        """
        st.title("🎙️ Join The Third Voice AI")
        st.subheader("Start your journey towards healthier conversations.")

        # Mission context
        st.markdown("""
        > *"When both people are speaking from pain, someone must be the third voice."*
        **Join thousands rebuilding their most important relationships.**
        """)

        with st.form("signup_form"):
            email = show_form_input("Email", "signup_email")
            password = show_form_input(
                "Password (minimum 6 characters)",
                "signup_password",
                input_type="password"
            )
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
        if show_navigation_button("Go to Login", "go_to_login_btn"):
            state_manager.set_app_mode("login")
            st.rerun()

        # Preview what they'll get
        AuthUI._show_signup_benefits()

    @staticmethod
    def show_verification_notice(auth_manager, state_manager) -> None:
        """
        Display verification notice page
        """
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
            if show_navigation_button("📨 Resend Verification Email", "resend_verification_btn"):
                if auth_manager.resend_verification(email):
                    display_success("Verification email resent!")
                else:
                    display_error("Could not resend email. Please try signing up again if needed.")
        with col2:
            if show_navigation_button("🔑 Go to Login", "go_to_login_from_verification_btn"):
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
        AuthUI._show_post_verification_preview()

    @staticmethod
    def _show_mission_context() -> None:
        """Show mission context in expandable section"""
        with st.expander("💙 Our Mission", expanded=False):
            st.markdown("""
            **The Third Voice AI** was born from communication breakdowns that shattered a family.
            We're turning pain into purpose, helping families heal through better conversations.
            Built with love by Predrag Mirkovic, fighting to return to his 6-year-old daughter Samantha
            after 15 months apart. Every feature serves family healing.
            """)

    @staticmethod
    def _show_signup_benefits() -> None:
        """Show signup benefits in expandable section"""
        with st.expander("✨ What you'll get access to", expanded=True):
            st.markdown("""
            **🌟 Transform difficult conversations** - Turn anger into understanding
            **💕 Multi-relationship support** - Romantic, family, workplace, co-parenting, friendships
            **🎯 Context-aware guidance** - AI understands your specific relationship dynamics
            **📊 Healing progress tracking** - See your communication improvement over time
            **💾 Conversation history** - Access all your guided conversations anytime
            **🚀 Always improving** - Built by a father fighting to heal his own family
            """)

    @staticmethod
    def _show_post_verification_preview() -> None:
        """Show post-verification preview in expandable section"""
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
