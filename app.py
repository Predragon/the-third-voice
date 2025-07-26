"""
Authentication Debug & Fix - The Third Voice AI
Run this to debug auth issues after modularization
"""

import streamlit as st

def debug_modular_auth():
    """Debug authentication issues in the modular version"""
    
    st.title("🔧 Modular Auth Debug")
    st.markdown("Let's fix the authentication after modularization...")
    
    # Test 1: Check if imports work
    st.subheader("1. Testing Module Imports")
    
    try:
        from data_backend import sign_in, sign_up, get_current_user_id, restore_user_session
        st.success("✅ data_backend imports working")
    except Exception as e:
        st.error(f"❌ data_backend import failed: {e}")
        st.code(str(e))
        return
    
    try:
        from ui_components import render_login_form
        st.success("✅ ui_components imports working")
    except Exception as e:
        st.error(f"❌ ui_components import failed: {e}")
        st.code(str(e))
        return
    
    # Test 2: Check session state
    st.subheader("2. Current Session State")
    st.json({
        "authenticated": st.session_state.get("authenticated", "NOT SET"),
        "user": str(st.session_state.get("user", "NOT SET"))[:100],
        "app_mode": st.session_state.get("app_mode", "NOT SET")
    })
    
    # Test 3: Test the sign_in function directly
    st.subheader("3. Test Sign-In Function")
    
    with st.form("direct_signin_test"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        test_signin = st.form_submit_button("Test Direct Sign-In")
        
        if test_signin and email and password:
            st.write("Calling sign_in function...")
            
            # Show before state
            st.write("BEFORE:")
            st.json({
                "authenticated": st.session_state.get("authenticated"),
                "user": str(st.session_state.get("user"))[:50] if st.session_state.get("user") else None
            })
            
            # Call the function
            try:
                result = sign_in(email, password)
                st.write(f"sign_in returned: {result}")
                
                # Show after state
                st.write("AFTER:")
                st.json({
                    "authenticated": st.session_state.get("authenticated"),
                    "user": str(st.session_state.get("user"))[:50] if st.session_state.get("user") else None
                })
                
                if result:
                    st.success("✅ Sign-in function worked!")
                    st.balloons()
                else:
                    st.error("❌ Sign-in function returned False")
                    
            except Exception as e:
                st.error(f"❌ Sign-in function threw exception: {e}")
                st.exception(e)
    
    # Test 4: Check Supabase connection
    st.subheader("4. Direct Supabase Test")
    
    if st.button("Test Supabase Directly"):
        try:
            from data_backend import get_supabase
            supabase = get_supabase()
            
            # Test with actual credentials if provided
            if 'test_email' in st.session_state and 'test_password' in st.session_state:
                email = st.session_state.test_email
                password = st.session_state.test_password
                
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    st.success(f"✅ Direct Supabase login works! User: {response.user.email}")
                else:
                    st.error("❌ Direct Supabase login failed")
                    st.write(f"Response: {response}")
            else:
                st.info("Enter credentials above first, then try this test")
                
        except Exception as e:
            st.error(f"❌ Direct Supabase test failed: {e}")
            st.exception(e)

def show_fixed_login_form():
    """Show a fixed version of the login form"""
    
    st.subheader("5. Fixed Login Form")
    st.markdown("Try this corrected version:")
    
    with st.form("fixed_login_form"):
        email = st.text_input("Email", key="fixed_email")
        password = st.text_input("Password", type="password", key="fixed_password")
        login_button = st.form_submit_button("Login (Fixed)")
        
        if login_button:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                # Store for other tests
                st.session_state.test_email = email
                st.session_state.test_password = password
                
                try:
                    # Import here to avoid circular imports
                    from data_backend import get_supabase
                    
                    supabase = get_supabase()
                    
                    with st.spinner("Logging in..."):
                        response = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                    
                    # Check the response structure
                    st.write("Raw response structure:")
                    st.write(f"Has user: {hasattr(response, 'user')}")
                    st.write(f"Has error: {hasattr(response, 'error')}")
                    
                    if hasattr(response, 'user') and response.user:
                        # Update session state manually
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        st.session_state.app_mode = "contacts_list"
                        
                        st.success(f"✅ LOGIN SUCCESS! Welcome {response.user.email}")
                        st.success("Session state updated - try refreshing the page")
                        
                    elif hasattr(response, 'error') and response.error:
                        st.error(f"❌ Login failed: {response.error.message}")
                        
                        # Specific error help
                        if "invalid_credentials" in response.error.message.lower():
                            st.info("💡 This usually means wrong email/password or unverified email")
                        elif "email_not_confirmed" in response.error.message.lower():
                            st.info("💡 Check your email for verification link")
                            
                    else:
                        st.error("❌ Unexpected response format")
                        st.json(response.__dict__ if hasattr(response, '__dict__') else str(response))
                        
                except Exception as e:
                    st.error(f"❌ Login exception: {e}")
                    st.exception(e)

def show_working_app_structure():
    """Show the corrected app structure"""
    
    st.subheader("6. App Structure Fix")
    
    st.markdown("""
    **The issue is likely in app.py session management. Here's the fix:**
    
    In your `app.py`, make sure the main() function looks like this:
    """)
    
    st.code("""
def main():
    # Initialize session state FIRST
    initialize_session_state()
    
    # Try to restore session BEFORE routing
    if not st.session_state.authenticated:
        if restore_user_session():
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    
    # Load data if authenticated
    if st.session_state.authenticated and not st.session_state.contacts:
        st.session_state.contacts = load_contacts_and_history()
    
    # Then do routing...
    if st.session_state.app_mode == "login":
        render_login_form()
    # ... etc
""", language="python")
    
    st.markdown("""
    **Key fixes:**
    1. Session state initialization happens FIRST
    2. Session restoration happens BEFORE routing
    3. Data loading only happens when authenticated
    """)

# Run the debug
if __name__ == "__main__":
    debug_modular_auth()
    st.markdown("---")
    show_fixed_login_form()
    st.markdown("---")  
    show_working_app_structure()
