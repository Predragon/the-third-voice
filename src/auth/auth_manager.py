"""
Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
Enhanced with session persistence and Google Sign-In
"""

import streamlit as st
from typing import Optional, Tuple
from src.config.settings import AppConfig


class AuthManager:
    """Handle authentication workflows"""
    
    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
        print(f"Debug: Supabase client initialized: {self.supabase}")
        self._check_existing_session()
    
    def _check_existing_session(self):
        """Check if there's an existing Supabase session"""
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
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
    
    def sign_in_with_google(self):
        """Initiate Google Sign-In with proper PKCE OAuth flow"""
        try:
            print("Debug: Initiating Google OAuth with PKCE")
            
            # Get current app URL for redirect
            current_url = "https://the-third-voice.streamlit.app"
            
            print(f"Debug: Redirect URL: {current_url}")
            
            # Use Supabase's OAuth method with PKCE
            response = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": current_url,
                    "scopes": "openid email profile"
                }
            })
            
            if hasattr(response, 'url') and response.url:
                print(f"Debug: OAuth URL generated: {response.url[:50]}...")
                
                # Store the current URL in session state for callback verification
                st.session_state.oauth_redirect_url = current_url
                
                # Redirect using JavaScript
                st.markdown(f"""
                <script>
                    window.location.href = "{response.url}";
                </script>
                """, unsafe_allow_html=True)
                
                # Fallback link
                st.markdown(f"[Click here if not redirected automatically]({response.url})")
                st.stop()
            else:
                st.error("Failed to generate Google OAuth URL")
                print(f"Debug: OAuth response: {response}")
                
        except Exception as e:
            st.error(f"Google sign-in error: {str(e)}")
            print(f"Debug: Google sign-in error: {str(e)}")
    
    def handle_google_callback(self):
        """Handle Google OAuth callback with PKCE support"""
        print("Debug: Checking for OAuth callback")
        
        # Get all query parameters
        query_params = dict(st.query_params)
        print(f"Debug: Query params: {query_params}")
        
        if not query_params:
            print("Debug: No query parameters found")
            return None
            
        # Check for authorization code
        if "code" in query_params:
            auth_code = query_params["code"]
            print(f"Debug: Found OAuth code: {auth_code[:20]}...")
            
            try:
                # For PKCE flow with your Supabase client version
                print("Debug: Processing OAuth callback with PKCE")
                
                # Get code_verifier from query params or session state
                code_verifier = query_params.get("code_verifier", "")
                
                print(f"Debug: Code verifier: {code_verifier[:20] if code_verifier else 'None'}...")
                
                # Try the exchange with proper parameters
                response = self.supabase.auth.exchange_code_for_session({
                    "auth_code": auth_code,
                    "code_verifier": code_verifier
                })
                
                if hasattr(response, 'user') and response.user:
                    st.session_state.user = response.user
                    st.session_state.session = response.session if hasattr(response, 'session') else None
                    print(f"✅ User authenticated: {response.user.email}")
                    
                    # Clear query params to prevent re-processing
                    st.query_params.clear()
                    st.rerun()
                    return response.user
                else:
                    print("Debug: No user in response")
                    st.error("Authentication failed - no user returned")
                    
            except Exception as e:
                print(f"Debug: PKCE authentication failed: {str(e)}")
                
                # Fallback: Try without code_verifier for older flows
                try:
                    print("Debug: Trying fallback method without PKCE")
                    response = self.supabase.auth.exchange_code_for_session({
                        "auth_code": auth_code
                    })
                    
                    if hasattr(response, 'user') and response.user:
                        st.session_state.user = response.user
                        print(f"✅ User authenticated via fallback: {response.user.email}")
                        st.query_params.clear()
                        st.rerun()
                        return response.user
                        
                except Exception as e2:
                    print(f"Debug: Fallback also failed: {str(e2)}")
                    
                    # Final attempt: Try manual token exchange
                    try:
                        print("Debug: Trying manual token exchange")
                        import requests
                        
                        # Make direct request to Supabase token endpoint
                        token_url = f"{AppConfig.get_supabase_url()}/auth/v1/token"
                        
                        data = {
                            "grant_type": "authorization_code",
                            "code": auth_code,
                            "redirect_uri": "https://the-third-voice.streamlit.app"
                        }
                        
                        headers = {
                            "apikey": AppConfig.get_supabase_key(),
                            "Content-Type": "application/x-www-form-urlencoded"
                        }
                        
                        token_response = requests.post(token_url, data=data, headers=headers)
                        
                        if token_response.status_code == 200:
                            token_data = token_response.json()
                            access_token = token_data.get("access_token")
                            
                            if access_token:
                                # Set session with the token
                                auth_response = self.supabase.auth.set_session(access_token, token_data.get("refresh_token", ""))
                                
                                if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                                    st.session_state.user = auth_response.user
                                    print(f"✅ User authenticated via manual exchange: {auth_response.user.email}")
                                    st.query_params.clear()
                                    st.rerun()
                                    return auth_response.user
                        
                        print(f"Debug: Manual exchange failed with status: {token_response.status_code}")
                        
                    except Exception as e3:
                        print(f"Debug: Manual exchange failed: {str(e3)}")
                        
                    st.error(f"OAuth authentication failed: {str(e)}")exchange method
                try:
                    print("Debug: Trying fallback method")
                    response = self.supabase.auth.exchange_code_for_session({
                        "auth_code": auth_code
                    })
                    
                    if hasattr(response, 'user') and response.user:
                        st.session_state.user = response.user
                        print(f"✅ User authenticated via fallback: {response.user.email}")
                        st.query_params.clear()
                        st.rerun()
                        return response.user
                        
                except Exception as e2:
                    print(f"Debug: Fallback also failed: {str(e2)}")
                    st.error(f"OAuth authentication failed: {str(e)}")
        
        # Check for access token (implicit flow)
        elif "access_token" in query_params:
            access_token = query_params["access_token"]
            refresh_token = query_params.get("refresh_token", "")
            print(f"Debug: Found access token: {access_token[:20]}...")
            
            try:
                response = self.supabase.auth.set_session(access_token, refresh_token)
                
                if response and hasattr(response, 'user') and response.user:
                    st.session_state.user = response.user
                    print(f"✅ User authenticated via access token: {response.user.email}")
                    st.query_params.clear()
                    st.rerun()
                    return response.user
                    
            except Exception as e:
                print(f"Debug: Access token method failed: {str(e)}")
                st.error(f"Access token authentication failed: {str(e)}")
        
        # Check for errors
        elif "error" in query_params:
            error = query_params["error"]
            error_description = query_params.get("error_description", "No description")
            print(f"Debug: OAuth error: {error} - {error_description}")
            st.error(f"OAuth error: {error}")
            
        return None
    
    def sign_out(self):
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Clear query params
            st.query_params.clear()
            print("✅ User signed out successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Sign out error: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # First handle OAuth callback if present
        if dict(st.query_params):
            self.handle_google_callback()
        
        # Check session state first
        if hasattr(st.session_state, 'user') and st.session_state.user is not None:
            print(f"Debug: User found in session state: {st.session_state.user.email}")
            return True
            
        # Check Supabase session as fallback
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                print(f"Debug: User found in Supabase session: {session.user.email}")
                return True
            else:
                print("Debug: No active session")
                
        except Exception as e:
            print(f"Debug: Session check error: {str(e)}")
            
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
