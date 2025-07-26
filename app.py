"""
Direct Login Test - Bypass all the complex routing
This should work if the authentication itself is working
"""

import streamlit as st
from data_backend import get_supabase, load_contacts_and_history

def direct_login_test():
    """Test login with direct session management"""
    
    # Initialize minimal session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.contacts = {}
    
    st.title("🎙️ The Third Voice AI - Direct Login Test")
    
    if st.session_state.authenticated:
        # Show authenticated state
        st.success(f"✅ Logged in as: {st.session_state.user.email}")
        
        if st.button("Load Contacts"):
            st.session_state.contacts = load_contacts_and_history()
            st.success(f"Loaded {len(st.session_state.contacts)} contacts")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.contacts = {}
            st.rerun()
        
        # Show contacts if any
        if st.session_state.contacts:
            st.subheader("Your Contacts:")
            for name, data in st.session_state.contacts.items():
                st.write(f"• {name} ({data['context']})")
    
    else:
        # Show login form
        st.subheader("Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                try:
                    # Direct Supabase call
                    supabase = get_supabase()
                    
                    with st.spinner("Logging in..."):
                        response = supabase.auth.sign_in_with_password({
                            "email": email, 
                            "password": password
                        })
                    
                    if response.user:
                        # Direct session state update
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        
                        st.success(f"✅ Login successful! Welcome {response.user.email}")
                        st.balloons()
                        
                        # Immediate rerun
                        st.rerun()
                        
                    elif response.error:
                        st.error(f"❌ Login failed: {response.error.message}")
                    else:
                        st.error("❌ Login failed: Unknown error")
                        
                except Exception as e:
                    st.error(f"❌ Login exception: {e}")
                    st.exception(e)

if __name__ == "__main__":
    direct_login_test()
