"""
Authentication Manager for The Third Voice AI
TRUE SUPABASE-CENTRIC APPROACH with direct Google OAuth implementation
"""

import streamlit as st
import time
from typing import Optional, Tuple
from src.config.settings import AppConfig


class AuthManager:
    """Handle authentication workflows using direct Supabase implementation"""
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        self.supabase_url = AppConfig.get_supabase_url()
        self.supabase_key = AppConfig.get_supabase_key()
        
        # Initialize auth with proper settings
        self._initialize_auth_client()
    
    def _initialize_auth_client(self):
        """Initialize Supabase auth client with proper settings"""
        try:
            # Configure client options for better session handling
            from supabase.lib.client_options import ClientOptions
            
            client_options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
                detect_session_in_url=True
            )
            
            # Reinitialize with new options
            self.supabase.auth.client_options = client_options
            
            # Try to recover existing session
            self.supabase.auth.initialize()
            
        except Exception as e:
            print(f"Supabase auth initialization warning: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check authentication - ALWAYS checks Supabase first"""
        try:
            # First try to get existing session
            session = self.supabase.auth.get_session()
            
            # If no session, check URL for OAuth callback
            if not session:
                session = self.supabase.auth.get_session_from_url()
            
            if session and session.user:
                # User is authenticated in Supabase
                self._update_session_state_cache(session)
                print(f"✅ User authenticated via Supabase: {session.user.email}")
                return True
            
            # No valid session found
            self._clear_session_state()
            return False
            
        except Exception as e:
            print(f"⚠️ Supabase session check error: {str(e)}")
            self._clear_session_state()
            return False
    
    def _update_session_state_cache(self, session):
        """Update session state as a cache (not source of truth)"""
        try:
            user = session.user
            user_metadata = user.user_metadata or {}
            
            st.session_state.user = user
            st.session_state.authenticated = True
            st.session_state.user_name = user_metadata.get('name') or user_metadata.get('full_name')
            st.session_state.user_email = user.email
            st.session_state.avatar_url = user_metadata.get('avatar_url')
            
        except Exception as e:
            print(f"⚠️ Error updating session state cache: {str(e)}")
    
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
    
    def render_google_login(self) -> bool:
        """Render Google OAuth login using direct Supabase implementation"""
        # Create the Google OAuth URL
        google_auth_url = f"{self.supabase_url}/auth/v1/authorize?provider=google"
        
        # Render the login button
        if st.button("Sign in with Google", key="google_signin", use_container_width=True):
            # Store the current page URL to redirect back after auth
            st.session_state.pre_auth_page = st.query_params
            
            # Redirect to Google OAuth
            st.markdown(f"""
            <a href="{google_auth_url}" target="_blank">
                <button style="visibility:hidden;" id="googleAuthButton">
                    Sign in with Google
                </button>
            </a>
            <script>
                document.getElementById('googleAuthButton').click();
            </script>
            """, unsafe_allow_html=True)
            
            # Check for authentication in a loop
            with st.spinner("Waiting for Google sign in to complete..."):
                for _ in range(15):  # Check for 15 seconds max
                    if self.is_authenticated():
                        st.success("✅ Successfully signed in with Google!")
                        time.sleep(1)
                        st.rerun()
                    time.sleep(1)
                else:
                    st.error("Timed out waiting for Google sign in")
        
        return False
    
    def handle_oauth_callback(self) -> bool:
        """Handle OAuth callback parameters in URL"""
        try:
            query_params = st.query_params
            
            # Check for Supabase OAuth callback
            if 'access_token' in query_params or 'refresh_token' in query_params:
                st.info("🔄 Processing authentication...")
                
                # Extract tokens from URL
                access_token = query_params.get('access_token', [''])[0]
                refresh_token = query_params.get('refresh_token', [''])[0]
                
                if access_token and refresh_token:
                    # Set the session directly
                    self.supabase.auth.set_session(access_token, refresh_token)
                    
                    # Verify authentication
                    if self.is_authenticated():
                        # Clean URL and redirect
                        self._clean_url_and_redirect()
                        return True
                
                st.error("❌ Authentication failed. Please try again.")
                self._clean_url_and_redirect()
                return False
                
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
        
        return False
    
    def _clean_url_and_redirect(self):
        """Clean OAuth parameters from URL"""
        # Get the original URL before auth if available
        redirect_url = st.session_state.get('pre_auth_page', {})
        
        # Clean the URL
        st.markdown("""
        <script>
        if (window.location.search || window.location.hash) {
            const url = new URL(window.location);
            url.search = '';
            url.hash = '';
            window.history.replaceState({}, document.title, url.toString());
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Rerun to update the UI
        time.sleep(0.5)
        st.rerun()
    
    def render_logout_button(self, location="sidebar"):
        """Render the logout button with user info"""
        try:
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
        user_name = self.get_current_user_name()
        user_email = self.get_current_user_email()
        avatar_url = self.get_avatar_url()
        
        if user_name:
            st.write(f"👋 Welcome {user_name}!")
        elif user_email:
            st.write(f"👋 Welcome {user_email}!")
        
        if avatar_url:
            st.image(avatar_url, width=60)
        
        if st.button("Sign Out", key="sign_out_button", use_container_width=True):
            self.sign_out()
    
    def sign_out(self):
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            self._clear_session_state()
            st.success("✅ Signed out successfully")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Sign out error: {str(e)}")
    
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