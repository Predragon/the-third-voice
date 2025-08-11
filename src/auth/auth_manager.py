"""
Authentication Manager for The Third Voice AI
Handle authentication workflows with Supabase
Enhanced with session persistence and Google Sign-In
Fixed OAuth state persistence issue
"""

import streamlit as st
from typing import Optional, Tuple
import hashlib
import base64
import secrets
import time
import json
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
    
    def _generate_pkce_challenge(self):
        """Generate PKCE code verifier and challenge"""
        # Generate code verifier (random string)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def _store_oauth_state(self, code_verifier: str, state: str):
        """Store OAuth state in database for persistence across redirects"""
        try:
            # Create a temporary OAuth state record
            oauth_data = {
                'state': state,
                'code_verifier': code_verifier,
                'created_at': int(time.time()),
                'expires_at': int(time.time() + 600)  # 10 minutes expiry
            }
            
            # Store in a temporary table or use browser's URL state parameter
            # For now, we'll encode it in the state parameter itself
            encoded_data = base64.urlsafe_b64encode(
                json.dumps(oauth_data).encode('utf-8')
            ).decode('utf-8')
            
            return encoded_data
            
        except Exception as e:
            print(f"Error storing OAuth state: {str(e)}")
            return state
    
    def _retrieve_oauth_state(self, state: str):
        """Retrieve OAuth state from encoded state parameter"""
        try:
            # Try to decode the state parameter
            decoded_data = json.loads(
                base64.urlsafe_b64decode(state.encode('utf-8')).decode('utf-8')
            )
            
            # Check if it's expired
            if decoded_data.get('expires_at', 0) < int(time.time()):
                print("OAuth state expired")
                return None
                
            return decoded_data.get('code_verifier')
            
        except Exception as e:
            print(f"Error retrieving OAuth state: {str(e)}")
            return None
    
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
            
            # Generate PKCE challenge and state
            code_verifier, code_challenge = self._generate_pkce_challenge()
            oauth_state = secrets.token_urlsafe(32)
            
            # Store OAuth state with code verifier encoded in state parameter
            encoded_state = self._store_oauth_state(code_verifier, oauth_state)
            
            print(f"Debug: Generated PKCE challenge: {code_challenge[:20]}...")
            print(f"Debug: Generated state: {oauth_state[:20]}...")
            
            # Get current app URL for redirect
            current_url = "https://the-third-voice.streamlit.app"
            
            print(f"Debug: Redirect URL: {current_url}")
            
            # Use Supabase's OAuth method with PKCE and state
            response = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": current_url,
                    "scopes": "openid email profile",
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                    "state": encoded_state  # Include our encoded state
                }
            })
            
            if hasattr(response, 'url') and response.url:
                print(f"Debug: OAuth URL generated: {response.url[:50]}...")
                
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
        print(f"Debug: Query params: {list(query_params.keys())}")
        
        if not query_params:
            print("Debug: No query parameters found")
            return None
            
        # Check for authorization code
        if "code" in query_params:
            auth_code = query_params["code"]
            state = query_params.get("state", "")
            print(f"Debug: Found OAuth code: {auth_code[:20]}...")
            print(f"Debug: Found state: {state[:20] if state else 'None'}...")
            
            try:
                # Retrieve code_verifier from state parameter
                code_verifier = None
                if state:
                    code_verifier = self._retrieve_oauth_state(state)
                
                print(f"Debug: Retrieved code verifier: {code_verifier[:20] if code_verifier else 'None'}...")
                
                if not code_verifier:
                    print("Debug: No code verifier found, trying without PKCE")
                    # Try without PKCE as fallback
                    try:
                        response = self.supabase.auth.exchange_code_for_session({
                            "auth_code": auth_code
                        })
                        
                        if hasattr(response, 'user') and response.user:
                            st.session_state.user = response.user
                            print(f"✅ User authenticated without PKCE: {response.user.email}")
                            st.query_params.clear()
                            st.rerun()
                            return response.user
                            
                    except Exception as fallback_error:
                        print(f"Debug: Fallback without PKCE failed: {str(fallback_error)}")
                        
                        # Final fallback: Try manual token exchange
                        return self._manual_token_exchange(auth_code)
                else:
                    # Try PKCE flow first
                    try:
                        response = self.supabase.auth.exchange_code_for_session({
                            "auth_code": auth_code,
                            "code_verifier": code_verifier
                        })
                        
                        if hasattr(response, 'user') and response.user:
                            st.session_state.user = response.user
                            print(f"✅ User authenticated with PKCE: {response.user.email}")
                            st.query_params.clear()
                            st.rerun()
                            return response.user
                            
                    except Exception as pkce_error:
                        print(f"Debug: PKCE flow failed: {str(pkce_error)}")
                        
                        # Fallback to manual token exchange
                        return self._manual_token_exchange(auth_code)
                    
            except Exception as e:
                print(f"Debug: General OAuth error: {str(e)}")
                return self._manual_token_exchange(auth_code)
        
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
    
    def _manual_token_exchange(self, auth_code: str):
        """Manual token exchange as final fallback"""
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
                    auth_response = self.supabase.auth.set_session(
                        access_token, 
                        token_data.get("refresh_token", "")
                    )
                    
                    if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                        st.session_state.user = auth_response.user
                        print(f"✅ User authenticated via manual exchange: {auth_response.user.email}")
                        st.query_params.clear()
                        st.rerun()
                        return auth_response.user
            
            print(f"Debug: Manual exchange failed with status: {token_response.status_code}")
            if token_response.status_code != 200:
                print(f"Debug: Response content: {token_response.text}")
            
            # If all else fails, show user-friendly error
            st.error("Authentication failed. Please try signing in again.")
            
        except Exception as e3:
            print(f"Debug: Manual exchange failed: {str(e3)}")
            st.error("Authentication failed. Please try signing in again.")
            
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
            callback_result = self.handle_google_callback()
            if callback_result:
                return True
        
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
