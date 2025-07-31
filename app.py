# auth.py - The Third Voice AI Authentication
# Supabase authentication management with mobile-friendly error handling and persistent sessions

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
from .state_manager import state_manager
from .config import ERROR_MESSAGES

class AuthManager:
    """
    Authentication manager using Supabase
    Handles sign up, sign in, sign out with mobile-optimized UX and persistent sessions
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase = self._init_supabase()
        # Try to restore session on initialization
        self._try_restore_session()
    
    @st.cache_resource
    def _init_supabase(_self) -> Client:
        """Initialize Supabase connection with error handling"""
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            return create_client(url, key)
        except KeyError as e:
            st.error(ERROR_MESSAGES["no_supabase_config"])
            st.stop()
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {e}")
            st.stop()
    
    def _try_restore_session(self) -> None:
        """Try to restore session on app initialization"""
        try:
            # Check if we have stored session tokens in browser storage
            if hasattr(st, 'query_params'):
                # Get session from URL params if available (for email confirmations)
                params = st.query_params
                if 'access_token' in params and 'refresh_token' in params:
                    try:
                        self.supabase.auth.set_session(
                            params['access_token'], 
                            params['refresh_token']
                        )
                        # Clear URL params after setting session
                        st.query_params.clear()
                    except Exception as e:
                        st.warning(f"Could not restore session from URL: {e}")
            
            # Try to get existing session
            session = self.supabase.auth.get_session()
            if session and session.user:
                # Session exists, restore authentication state
                if not state_manager.is_authenticated():
                    state_manager.set_authenticated(session.user)
                    
                    # Import here to avoid circular imports
                    from .data_manager import data_manager
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    
                    if contacts:
                        state_manager.set_app_mode("contacts_list")
                    else:
                        state_manager.set_app_mode("first_time_setup")
            else:
                # Try to refresh the session if refresh token exists
                try:
                    refreshed_session = self.supabase.auth.refresh_session()
                    if refreshed_session and refreshed_session.user:
                        state_manager.set_authenticated(refreshed_session.user)
                        
                        from .data_manager import data_manager
                        contacts = data_manager.load_contacts_and_history()
                        state_manager.set_contacts(contacts)
                        
                        if contacts:
                            state_manager.set_app_mode("contacts_list")
                        else:
                            state_manager.set_app_mode("first_time_setup")
                except Exception:
                    # Refresh failed, user needs to log in again
                    pass
                    
        except Exception as e:
            # Session restoration failed, but don't show error to user
            # They'll just need to log in again
            pass
    
    def get_current_user_id(self) -> Optional[str]:
        """Get the current authenticated user's ID"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                return session.user.id
            return None
        except Exception as e:
            st.error(f"Error getting user session: {e}")
            return None
    
    def restore_session(self) -> bool:
        """
        Restore user session on app reload
        Returns True if session was restored, False otherwise
        """
        try:
            # First try to refresh the session
            try:
                refreshed_session = self.supabase.auth.refresh_session()
                if refreshed_session and refreshed_session.user:
                    if not state_manager.is_authenticated():
                        state_manager.set_authenticated(refreshed_session.user)
                        
                        # Import here to avoid circular imports
                        from .data_manager import data_manager
                        contacts = data_manager.load_contacts_and_history()
                        state_manager.set_contacts(contacts)
                        
                        if contacts:
                            state_manager.set_app_mode("contacts_list")
                        else:
                            state_manager.set_app_mode("first_time_setup")
                        
                        return True
            except Exception:
                pass
            
            # If refresh failed, try to get existing session
            session = self.supabase.auth.get_session()
            if session and session.user:
                if not state_manager.is_authenticated():
                    state_manager.set_authenticated(session.user)
                    
                    # Import here to avoid circular imports
                    from .data_manager import data_manager
                    contacts = data_manager.load_contacts_and_history()
                    state_manager.set_contacts(contacts)
                    
                    if contacts:
                        state_manager.set_app_mode("contacts_list")
                    else:
                        state_manager.set_app_mode("first_time_setup")
                    
                    return True
            return False
        except Exception as e:
            # Don't show error to user, just return False
            return False
    
    def sign_up(self, email: str, password: str) -> bool:
        """
        Sign up new user
        Returns True if successful, False otherwise
        """
        try:
            response = self.supabase.auth.sign_up({"email": email, "password": password})
            if response.user:
                state_manager.set_verification_notice(email)
                return True
            elif response.error:
                state_manager.set_error(f"Sign-up failed: {response.error.message}")
                return False
        except Exception as e:
            state_manager.set_error(f"An unexpected error occurred during sign-up: {e}")
            return False
        
        return False
    
    def sign_in(self, email: str, password: str) -> bool:
        """
        Sign in existing user
        Returns True if successful, False otherwise
        """
        try:
            response = self.supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                state_manager.set_authenticated(response.user)
                
                # Load user data
                from .data_manager import data_manager
                contacts = data_manager.load_contacts_and_history()
                state_manager.set_contacts(contacts)
                
                if not contacts:
                    state_manager.set_app_mode("first_time_setup")
                else:
                    state_manager.set_app_mode("contacts_list")
                
                st.success(f"Welcome back, {response.user.email}!")
                return True
            elif response.error:
                state_manager.set_error(f"Login failed: {response.error.message}")
                return False
        except Exception as e:
            state_manager.set_error(f"An unexpected error occurred during login: {e}")
            return False
        
        return False
    
    def sign_out(self) -> bool:
        """
        Sign out current user
        Returns True if successful, False otherwise
        """
        try:
            response = self.supabase.auth.sign_out()
            if not response.error:
                # Clear session state
                state_manager.clear_authentication()
                
                # Clear any cached data
                from .data_manager import data_manager
                data_manager.clear_cache()
                
                st.info("You have been logged out.")
                return True
            else:
                state_manager.set_error(f"Logout failed: {response.error.message}")
                return False
        except Exception as e:
            state_manager.set_error(f"An unexpected error occurred during logout: {e}")
            return False
    
    def resend_verification(self, email: str) -> bool:
        """
        Resend verification email
        Returns True if successful, False otherwise
        """
        try:
            self.supabase.auth.resend({"type": "signup", "email": email})
            st.success("Verification email resent!")
            return True
        except Exception as e:
            st.warning("Could not resend email. Please try signing up again if needed.")
            return False

# Global auth manager instance
auth_manager = AuthManager()
