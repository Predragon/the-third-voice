"""
Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
Enhanced with streamlit-supabase-auth package for reliable OAuth
FIXED: Google OAuth redirect and email/password compatibility
"""

import streamlit as st
from typing import Optional, Tuple
from streamlit_supabase_auth import login_form, logout_button
from src.config.settings import AppConfig


class AuthManager:
    """Handle authentication workflows using streamlit-supabase-auth"""
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        self.supabase_url = AppConfig.get_supabase_url()
        self.supabase_key = AppConfig.get_supabase_key()
        print(f"Debug: Supabase client initialized: {self.supabase}")
        self._check_existing_session()
    
    def _check_existing_session(self):
        """Check if there's an existing Supabase session"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                if not hasattr(st.session_state, 'user') or st.session_state.user is None:
                    st.session_state.user = session.user
                    st.session_state.authenticated = True
                    # Store user info
                    user_metadata = session.user.user_metadata or {}
                    st.session_state.user_name = user_metadata.get('name') or user_metadata.get('full_name')
                    st.session_state.user_email = session.user.email
                    st.session_state.avatar_url = user_metadata.get('avatar_url')
                    print(f"✅ Restored session for user: {session.user.email}")
        except Exception as e:
            print(f"⚠️ Could not check existing session: {str(e)}")
    
    def render_login_form(self):
        """Render the streamlit-supabase-auth login form for Google OAuth only"""
        try:
            # Use the streamlit-supabase-auth login form
            session = login_form(
                url=self.supabase_url,
                apiKey=self.supabase_key,
                providers=["google"],  # Only Google for OAuth
            )
            
            if session:
                # Extract user information from session
                user = session.get('user', {})
                user_metadata = user.get('user_metadata', {})
                
                user_name = user_metadata.get('name') or user_metadata.get('full_name')
                email = user.get('email')
                avatar_url = user_metadata.get('avatar_url')
                email_verified = user_metadata.get('email_verified', True)  # Default to True for Google
                
                print(f"✅ User authenticated via streamlit-supabase-auth: {email}")
                
                # Check email verification (optional - Google emails are usually verified)
                if not email_verified:
                    st.error("Please use a verified email address to log in.")
                    return None
                
                # Store user information in session state
                st.session_state.user = user
                st.session_state.session = session
                st.session_state.authenticated = True
                st.session_state.user_name = user_name
                st.session_state.user_email = email
                st.session_state.avatar_url = avatar_url
                
                return session
            
            return None
            
        except Exception as e:
            st.error(f"Google authentication error: {str(e)}")
            print(f"Debug: Login form error: {str(e)}")
            return None
    
    def render_logout_button(self, location="sidebar"):
        """Render the logout button with user info
        
        Args:
            location: "sidebar" or "main" - where to render the logout UI
        """
        try:
            if location == "sidebar":
                with st.sidebar:
                    self._render_user_info_and_logout()
            else:
                self._render_user_info_and_logout()
                    
        except Exception as e:
            print(f"Debug: Logout button error: {str(e)}")
    
    def _render_user_info_and_logout(self):
        """Internal method to render user info and logout button"""
        # Display user info
        if hasattr(st.session_state, 'user_name') and st.session_state.user_name:
            st.write(f"👋 Welcome {st.session_state.user_name}!")
        elif hasattr(st.session_state, 'user_email') and st.session_state.user_email:
            st.write(f"👋 Welcome!")
        
        if hasattr(st.session_state, 'avatar_url') and st.session_state.avatar_url:
            st.image(st.session_state.avatar_url, width=60)
        
        # Render logout button
        if logout_button(url=self.supabase_url, apiKey=self.supabase_key):
            # Clear session state on logout
            self._clear_session_state()
            st.rerun()
    
    def _clear_session_state(self):
        """Clear all authentication-related session state"""
        keys_to_clear = [
            'user', 'session', 'authenticated', 'user_name', 
            'user_email', 'avatar_url', 'onboarding_completed'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        print("✅ Session state cleared")
    
    def sign_up(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user (traditional email/password)"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            if response.user:
                return True, "✅ Account created! Check your email for verification link!"
            else:
                return False, "❌ Sign up failed - please try again"
        except Exception as e:
            error_msg = str(e).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                return False, "❌ This email is already registered. Try signing in instead."
            elif "invalid email" in error_msg:
                return False, "❌ Please enter a valid email address"
            elif "password" in error_msg:
                return False, "❌ Password must be at least 6 characters"
            else:
                return False, f"❌ Sign up error: {str(e)}"
    
    def sign_in(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign in user (traditional email/password)"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Store user information in session state
                st.session_state.user = response.user
                st.session_state.authenticated = True
                st.session_state.user_email = response.user.email
                st.session_state.user_name = None  # Email login doesn't provide name
                st.session_state.avatar_url = None  # Email login doesn't provide avatar
                
                print(f"✅ User signed in via email: {response.user.email}")
                return True, "✅ Successfully signed in!"
            else:
                return False, "❌ Invalid email or password"
                
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                return False, "❌ Invalid email or password"
            elif "email not confirmed" in error_msg:
                return False, "❌ Please check your email and click the verification link first"
            else:
                return False, f"❌ Sign in error: {str(e)}"
    
    def sign_out(self):
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            self._clear_session_state()
            print("✅ User signed out successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Sign out error: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # Check session state first
        if (hasattr(st.session_state, 'authenticated') and 
            st.session_state.authenticated and 
            hasattr(st.session_state, 'user') and 
            st.session_state.user is not None):
            return True
            
        # Check Supabase session as fallback
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                # Restore session state
                st.session_state.user = session.user
                st.session_state.authenticated = True
                st.session_state.user_email = session.user.email
                
                # Try to get user metadata for name and avatar
                user_metadata = session.user.user_metadata or {}
                st.session_state.user_name = user_metadata.get('name') or user_metadata.get('full_name')
                st.session_state.avatar_url = user_metadata.get('avatar_url')
                
                print(f"Debug: User found in Supabase session: {session.user.email}")
                return True
        except Exception as e:
            print(f"Debug: Session check error: {str(e)}")
            
        return False
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.is_authenticated():
            user = st.session_state.user
            return user.get('id') if isinstance(user, dict) else user.id
        return None
    
    def get_current_user_email(self) -> Optional[str]:
        """Get current user email"""
        if self.is_authenticated():
            if hasattr(st.session_state, 'user_email'):
                return st.session_state.user_email
            user = st.session_state.user
            return user.get('email') if isinstance(user, dict) else user.email
        return None
    
    def get_current_user_name(self) -> Optional[str]:
        """Get current user name"""
        if hasattr(st.session_state, 'user_name'):
            return st.session_state.user_name
        return None
    
    def get_avatar_url(self) -> Optional[str]:
        """Get current user avatar URL"""
        if hasattr(st.session_state, 'avatar_url'):
            return st.session_state.avatar_url
        return None
