"""
Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
TRUE SUPABASE-CENTRIC APPROACH - Never trust session state
FIXED: OAuth redirect loop by making Supabase the single source of truth
"""

import streamlit as st
from typing import Optional, Tuple
from streamlit_supabase_auth import login_form, logout_button
from src.config.settings import AppConfig


class AuthManager:
    """Handle authentication workflows using TRUE Supabase-centric approach"""
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        self.supabase_url = AppConfig.get_supabase_url()
        self.supabase_key = AppConfig.get_supabase_key()
        print(f"Debug: Supabase client initialized: {self.supabase}")
        # Don't check existing session here - do it on demand only
    
    def is_authenticated(self) -> bool:
        """Check authentication - ALWAYS checks Supabase first, never trusts session state"""
        try:
            # ALWAYS query Supabase directly - this is the source of truth
            session = self.supabase.auth.get_session()
            
            if session and session.user:
                # User is authenticated in Supabase
                # Update session state as cache (not source of truth)
                self._update_session_state_cache(session)
                print(f"✅ User authenticated via Supabase: {session.user.email}")
                return True
            else:
                # No valid Supabase session
                self._clear_session_state()
                print("❌ No valid Supabase session found")
                return False
                
        except Exception as e:
            print(f"⚠️ Supabase session check error: {str(e)}")
            # On error, clear session state and return False
            self._clear_session_state()
            return False
    
    def _update_session_state_cache(self, session):
        """Update session state as a cache (not source of truth)"""
        try:
            user = session.user
            user_metadata = user.user_metadata or {}
            
            # Cache user info in session state for UI performance
            st.session_state.user = user
            st.session_state.authenticated = True
            st.session_state.user_name = user_metadata.get('name') or user_metadata.get('full_name')
            st.session_state.user_email = user.email
            st.session_state.avatar_url = user_metadata.get('avatar_url')
            
        except Exception as e:
            print(f"⚠️ Error updating session state cache: {str(e)}")
    
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
                # streamlit-supabase-auth returned a session
                # Don't trust it immediately - verify with our Supabase client
                print("🔄 streamlit-supabase-auth returned session, verifying...")
                
                # Force a recheck of authentication status
                if self.is_authenticated():
                    print("✅ Session verified with Supabase client")
                    return session
                else:
                    print("❌ Session not verified with Supabase client")
                    return None
            
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
            # Only render if actually authenticated (check Supabase first)
            if not self.is_authenticated():
                return
                
            if location == "sidebar":
                with st.sidebar:
                    self._render_user_info_and_logout()
            else:
                self._render_user_info_and_logout()
                    
        except Exception as e:
            print(f"Debug: Logout button error: {str(e)}")
    
    def _render_user_info_and_logout(self):
        """Internal method to render user info and logout button"""
        # Get current user info (from Supabase, cached in session state)
        user_name = self.get_current_user_name()
        user_email = self.get_current_user_email()
        avatar_url = self.get_avatar_url()
        
        # Display user info
        if user_name:
            st.write(f"👋 Welcome {user_name}!")
        elif user_email:
            st.write(f"👋 Welcome!")
        
        if avatar_url:
            st.image(avatar_url, width=60)
        
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
        
        print("🧹 Session state cleared")
    
    def sign_up(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user (traditional email/password)"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            if response.user:
                # Don't update session state here - let is_authenticated() handle it
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
                # Don't update session state here - let is_authenticated() handle it
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
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID - always from Supabase"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                return session.user.id
        except Exception as e:
            print(f"Error getting user ID: {str(e)}")
        return None
    
    def get_current_user_email(self) -> Optional[str]:
        """Get current user email - from session state cache if available, otherwise Supabase"""
        # Try session state cache first for performance
        if hasattr(st.session_state, 'user_email') and st.session_state.user_email:
            return st.session_state.user_email
            
        # Fallback to Supabase
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                return session.user.email
        except Exception as e:
            print(f"Error getting user email: {str(e)}")
        return None
    
    def get_current_user_name(self) -> Optional[str]:
        """Get current user name - from session state cache if available"""
        if hasattr(st.session_state, 'user_name') and st.session_state.user_name:
            return st.session_state.user_name
            
        # Try to get from Supabase if not in cache
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                user_metadata = session.user.user_metadata or {}
                name = user_metadata.get('name') or user_metadata.get('full_name')
                # Cache it for next time
                st.session_state.user_name = name
                return name
        except Exception as e:
            print(f"Error getting user name: {str(e)}")
        return None
    
    def get_avatar_url(self) -> Optional[str]:
        """Get current user avatar URL - from session state cache if available"""
        if hasattr(st.session_state, 'avatar_url') and st.session_state.avatar_url:
            return st.session_state.avatar_url
            
        # Try to get from Supabase if not in cache
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                user_metadata = session.user.user_metadata or {}
                avatar_url = user_metadata.get('avatar_url')
                # Cache it for next time
                st.session_state.avatar_url = avatar_url
                return avatar_url
        except Exception as e:
            print(f"Error getting avatar URL: {str(e)}")
        return None
