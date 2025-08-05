"""
Enhanced Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
Enhanced with better session persistence and recovery
"""

import streamlit as st
from typing import Optional, Tuple
import time


class AuthManager:
    """Handle authentication workflows with persistent sessions"""
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        # Check for existing session on initialization
        self._restore_session_on_startup()
    
    def _restore_session_on_startup(self):
        """Restore session from Supabase on app startup/refresh"""
        try:
            # Always check Supabase session first, regardless of session_state
            session = self.supabase.auth.get_session()
            
            if session and session.user:
                # Valid session found - restore to session_state
                st.session_state.user = session.user
                st.session_state.auth_restored = True
                print(f"✅ Session restored for user: {session.user.email}")
                return True
            else:
                # No valid session - clear any stale session_state
                if hasattr(st.session_state, 'user'):
                    delattr(st.session_state, 'user')
                print("ℹ️ No valid session found")
                return False
                
        except Exception as e:
            print(f"⚠️ Error restoring session: {str(e)}")
            # Clear potentially corrupted session state
            if hasattr(st.session_state, 'user'):
                delattr(st.session_state, 'user')
            return False
    
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
        """Sign in user with session persistence"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                # Store in session state
                st.session_state.user = response.user
                st.session_state.session = response.session
                print(f"✅ User signed in: {response.user.email}")
                return True, "Successfully signed in!"
            else:
                return False, "Invalid credentials"
                
        except Exception as e:
            error_msg = str(e)
            if "Invalid login credentials" in error_msg:
                return False, "Invalid email or password"
            elif "Email not confirmed" in error_msg:
                return False, "Please check your email and confirm your account"
            else:
                return False, f"Sign in error: {error_msg}"
    
    def sign_out(self):
        """Sign out user and clear all session data"""
        try:
            # Sign out from Supabase
            self.supabase.auth.sign_out()
            
            # Clear ALL session state
            keys_to_clear = list(st.session_state.keys())
            for key in keys_to_clear:
                del st.session_state[key]
            
            print("✅ User signed out successfully")
            
        except Exception as e:
            print(f"⚠️ Sign out error: {str(e)}")
            # Even if Supabase sign out fails, clear local session
            keys_to_clear = list(st.session_state.keys())
            for key in keys_to_clear:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with fallback to Supabase"""
        
        # First check session state
        if hasattr(st.session_state, 'user') and st.session_state.user is not None:
            # Verify the session is still valid by checking with Supabase occasionally
            if not hasattr(st.session_state, 'last_auth_check'):
                st.session_state.last_auth_check = time.time()
            
            # Check every 5 minutes
            if time.time() - st.session_state.last_auth_check > 300:
                if self._validate_current_session():
                    st.session_state.last_auth_check = time.time()
                    return True
                else:
                    return False
            
            return True
        
        # If not in session state, try to restore from Supabase
        return self._restore_session_on_startup()
    
    def _validate_current_session(self) -> bool:
        """Validate current session with Supabase"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                # Update session state if user info changed
                st.session_state.user = session.user
                return True
            else:
                # Session invalid - clear session state
                if hasattr(st.session_state, 'user'):
                    delattr(st.session_state, 'user')
                return False
        except:
            # On error, assume session invalid
            if hasattr(st.session_state, 'user'):
                delattr(st.session_state, 'user')
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
    
    def refresh_user_data(self):
        """Manually refresh user data from Supabase"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                return True
            return False
        except:
            return False
