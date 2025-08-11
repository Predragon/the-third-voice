import streamlit as st
from supabase import create_client, Client
import os
import json
from datetime import datetime

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    print(f"Debug: Supabase URL: {url}")
    print(f"Debug: Supabase Key: {key[:20]}..." if key else "No key found")
    return create_client(url, key)

supabase: Client = init_supabase()

def debug_current_state():
    """Debug current application state"""
    st.write("## 🔍 DEBUG INFORMATION")
    
    # Show current URL and query params
    query_params = dict(st.query_params)
    st.write("**Current URL Query Params:**", query_params)
    
    # Show session state
    st.write("**Streamlit Session State:**")
    session_state_dict = {}
    for key in st.session_state:
        if key in ['user', 'session']:
            session_state_dict[key] = str(st.session_state[key])[:100] + "..." if len(str(st.session_state[key])) > 100 else str(st.session_state[key])
        else:
            session_state_dict[key] = st.session_state[key]
    st.json(session_state_dict)
    
    # Check Supabase session
    st.write("**Supabase Session Check:**")
    try:
        session = supabase.auth.get_session()
        if session:
            st.success(f"✅ Supabase session exists")
            if hasattr(session, 'user') and session.user:
                st.write(f"User ID: {session.user.id}")
                st.write(f"Email: {session.user.email}")
            if hasattr(session, 'access_token'):
                st.write(f"Access token exists: {bool(session.access_token)}")
        else:
            st.error("❌ No Supabase session found")
    except Exception as e:
        st.error(f"❌ Supabase session error: {str(e)}")
    
    # Show environment variables (safely)
    st.write("**Environment Check:**")
    st.write(f"SUPABASE_URL exists: {bool(os.environ.get('SUPABASE_URL'))}")
    st.write(f"SUPABASE_ANON_KEY exists: {bool(os.environ.get('SUPABASE_ANON_KEY'))}")
    
    return query_params

def handle_oauth_callback(query_params):
    """Handle OAuth callback with detailed logging"""
    st.write("## 🔄 OAUTH CALLBACK HANDLER")
    
    if not query_params:
        st.info("ℹ️ No query parameters found")
        return False
    
    # Check for different possible parameters
    if "code" in query_params:
        auth_code = query_params["code"]
        st.success(f"✅ Found OAuth code: {auth_code[:20]}...")
        
        try:
            st.write("Attempting to exchange code for session...")
            
            # Method 1: Try exchange_code_for_session
            try:
                response = supabase.auth.exchange_code_for_session({
                    "auth_code": auth_code
                })
                st.write("Method 1 response:", type(response))
                
                if hasattr(response, 'user') and response.user:
                    st.success("✅ User authenticated via Method 1!")
                    st.session_state.user = response.user
                    st.session_state.session = response.session
                    st.query_params.clear()
                    return True
                    
            except Exception as e:
                st.warning(f"Method 1 failed: {str(e)}")
                
                # Method 2: Try different approach
                try:
                    st.write("Trying alternative method...")
                    # This might work depending on your Supabase client version
                    response = supabase.auth.get_session_from_url(st.experimental_get_query_params())
                    
                    if response and hasattr(response, 'user') and response.user:
                        st.success("✅ User authenticated via Method 2!")
                        st.session_state.user = response.user
                        st.session_state.session = response.session
                        st.query_params.clear()
                        return True
                        
                except Exception as e2:
                    st.error(f"Method 2 also failed: {str(e2)}")
                
        except Exception as main_e:
            st.error(f"❌ Authentication failed: {str(main_e)}")
    
    elif "access_token" in query_params:
        st.info("Found access_token in query params")
        access_token = query_params["access_token"]
        
        try:
            # Set the session with the access token
            response = supabase.auth.set_session(access_token, query_params.get("refresh_token", ""))
            
            if response and hasattr(response, 'user') and response.user:
                st.success("✅ User authenticated via access token!")
                st.session_state.user = response.user
                st.session_state.session = response.session
                st.query_params.clear()
                return True
                
        except Exception as e:
            st.error(f"❌ Access token authentication failed: {str(e)}")
    
    elif "error" in query_params:
        error = query_params["error"]
        error_description = query_params.get("error_description", "No description")
        st.error(f"❌ OAuth error: {error} - {error_description}")
    
    else:
        st.info("ℹ️ Query params found but no recognized OAuth parameters")
        st.write("Available params:", list(query_params.keys()))
    
    return False

def sign_in_with_google():
    """Initiate Google OAuth sign-in with debugging"""
    st.write("## 🚀 INITIATING GOOGLE SIGN-IN")
    
    try:
        # Get the current URL
        current_url = "http://localhost:8501"  # Default for local development
        
        # Try to get the actual URL if deployed
        try:
            import streamlit.web.cli as stcli
            current_url = f"https://{stcli.main._get_option('server.address')}:{stcli.main._get_option('server.port')}"
        except:
            pass
        
        st.write(f"Redirect URL will be: {current_url}")
        
        # Generate OAuth URL
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": current_url
            }
        })
        
        if hasattr(response, 'url') and response.url:
            st.success(f"✅ OAuth URL generated: {response.url[:50]}...")
            st.markdown(f"""
            <script>
                window.location.href = "{response.url}";
            </script>
            """, unsafe_allow_html=True)
            
            # Also provide a manual link as backup
            st.markdown(f"[Click here if not redirected automatically]({response.url})")
            st.stop()
        else:
            st.error("❌ Failed to generate OAuth URL")
            st.write("Response:", response)
            
    except Exception as e:
        st.error(f"❌ Sign-in error: {str(e)}")

def main():
    st.set_page_config(page_title="OAuth Debug", page_icon="🔍")
    
    st.title("🔍 OAuth Debug Mode")
    
    # Debug current state first
    query_params = debug_current_state()
    
    # Try to handle OAuth callback
    authenticated = handle_oauth_callback(query_params)
    
    if authenticated or (hasattr(st.session_state, 'user') and st.session_state.user):
        # User is authenticated
        st.success("## ✅ USER IS AUTHENTICATED!")
        
        if hasattr(st.session_state, 'user'):
            st.write(f"Welcome, {st.session_state.user.email}!")
            
        if st.button("Sign Out"):
            # Clear everything
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()
    else:
        # Show login
        st.write("## 🔐 LOGIN REQUIRED")
        
        if st.button("🔐 Sign in with Google"):
            sign_in_with_google()
        
        # Manual debug controls
        st.write("---")
        st.write("### Manual Debug Controls")
        
        if st.button("Clear All Session Data"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()
            
        if st.button("Refresh Page"):
            st.rerun()

if __name__ == "__main__":
    main()