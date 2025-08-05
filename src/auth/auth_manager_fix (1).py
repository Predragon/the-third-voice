"""
Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
Enhanced with session persistence
"""

import streamlit as st
from typing import Optional, Tuple


class AuthManager:
    """Handle authentication workflows"""
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        # Check for existing session on initialization
        self._check_existing_session()
    
    def _check_existing_session(self):
        """Check if there's an existing Supabase session"""
        try:
            # Get current session from Supabase
            session = self.supabase.auth.get_session()
            if session and session.user:
                # Store user in session state if not already there
                if not hasattr(st.session_state, 'user') or st.session_state.user is None:
                    st.session_state.user = session.user
                    print(f"✅ Restored session for user: {session.user.email}")
        except Exception as e:
            print(f"⚠️ Could not check existing session: {str(e)}")
    
    def sign_up(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign up a new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                return True, "Check your email for verification link!"
            else:
                return False, "Sign up failed"
                
        except Exception as e:
            return False, f"Sign up error: {str(e)}"
    
    def sign_in(self, email: str, password: str) -> Tuple[bool, str]:
        """Sign in user"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                st.session_state.user = response.user
                return True, "Successfully signed in!"
            else:
                return False, "Invalid credentials"
                
        except Exception as e:
            return False, f"Sign in error: {str(e)}"
    
    def sign_out(self):
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            print("✅ User signed out successfully")
        except Exception as e:
            st.error(f"Sign out error: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # First check session state
        if hasattr(st.session_state, 'user') and st.session_state.user is not None:
            return True
        
        # If not in session state, check Supabase session
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                return True
        except:
            pass
        
        return False
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.is_authenticated():
            return st.session_state.user.id
        return None
    
    def get_current_user_email(self) -> Optional[str]:
        """Get current user email"""
        if self.is_authenticated():
            return st.session_state.user.email
        return None