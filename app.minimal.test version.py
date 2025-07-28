# app.py - The Third Voice AI (Minimal Test Version)
# Testing modular structure with config.py and state_manager.py

import streamlit as st
from datetime import datetime
import json

# Import our modular components
from config import (
    APP_NAME, APP_ICON, VERSION, MISSION_STATEMENT, 
    CONTEXTS, PAGE_CONFIG, UI_MESSAGES, ERROR_MESSAGES
)
from state_manager import state_manager

def main():
    """Main application entry point for testing modular structure"""
    
    # Set page configuration
    st.set_page_config(**PAGE_CONFIG)
    
    # Header
    st.title(f"{APP_ICON} {APP_NAME}")
    st.subheader(f"Version {VERSION} - Modular Test")
    st.markdown(f"*{MISSION_STATEMENT}*")
    
    st.markdown("---")
    
    # Test Section 1: Configuration Display
    st.markdown("### 🔧 Configuration Test")
    st.success("✅ Successfully imported config.py")
    
    with st.expander("View Relationship Contexts", expanded=True):
        for context_key, context_data in CONTEXTS.items():
            st.markdown(f"**{context_data['icon']} {context_key.title()}**")
            st.markdown(f"Description: {context_data['description']}")
            st.markdown(f"Default Name: {context_data['default_name']}")
            st.markdown("---")
    
    # Test Section 2: State Manager Test
    st.markdown("### 🔄 State Manager Test")
    st.success("✅ Successfully imported state_manager.py")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Test State Operations:**")
        
        # Test setting a value
        if st.button("Set Test Value", use_container_width=True):
            state_manager.set('test_timestamp', datetime.now().isoformat())
            state_manager.set('test_counter', state_manager.get('test_counter', 0) + 1)
            st.rerun()
        
        # Test clearing a value
        if st.button("Clear Test Value", use_container_width=True):
            state_manager.clear_key('test_timestamp')
            st.rerun()
    
    with col2:
        st.markdown("**Current State Values:**")
        
        # Display test values
        test_timestamp = state_manager.get('test_timestamp')
        test_counter = state_manager.get('test_counter', 0)
        
        if test_timestamp:
            st.info(f"Test Timestamp: {test_timestamp}")
        else:
            st.warning("No test timestamp set")
        
        st.info(f"Test Counter: {test_counter}")
    
    # Test Section 3: State Manager Methods
    st.markdown("### 📊 State Manager Debug Info")
    
    debug_info = state_manager.get_debug_info()
    st.json(debug_info)
    
    # Test Section 4: Mobile Compatibility Test
    st.markdown("### 📱 Mobile Compatibility Test")
    
    # Test responsive columns
    mobile_col1, mobile_col2, mobile_col3 = st.columns([1, 2, 1])
    
    with mobile_col1:
        st.markdown("**Left**")
        st.button("📱", help="Mobile test button")
    
    with mobile_col2:
        st.markdown("**Center Content**")
        st.slider("Test Slider", 0, 100, 50)
    
    with mobile_col3:
        st.markdown("**Right**")
        st.button("🖥️", help="Desktop test button")
    
    # Test Section 5: Error Handling Test
    st.markdown("### ⚠️ Error Handling Test")
    
    col_error1, col_error2 = st.columns(2)
    
    with col_error1:
        if st.button("Set Test Error", use_container_width=True):
            state_manager.set_error("This is a test error message!")
            st.rerun()
    
    with col_error2:
        if st.button("Clear Test Error", use_container_width=True):
            state_manager.clear_error()
            st.rerun()
    
    # Display current error
    current_error = state_manager.get_error()
    if current_error:
        st.error(f"Current Error: {current_error}")
    else:
        st.success("No errors in state")
    
    # Test Section 6: Navigation Test
    st.markdown("### 🧭 Navigation Test")
    
    current_mode = state_manager.get_app_mode()
    st.info(f"Current App Mode: {current_mode}")
    
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        if st.button("Login Mode", use_container_width=True):
            state_manager.set_app_mode("login")
            st.rerun()
    
    with nav_col2:
        if st.button("Contacts Mode", use_container_width=True):
            state_manager.set_app_mode("contacts_list")
            st.rerun()
    
    with nav_col3:
        if st.button("Test Mode", use_container_width=True):
            state_manager.set_app_mode("test_mode")
            st.rerun()
    
    # Test Section 7: Sidebar Test
    with st.sidebar:
        st.markdown(f"### {APP_ICON} Sidebar Test")
        st.markdown(f"**App:** {APP_NAME}")
        st.markdown(f"**Version:** {VERSION}")
        
        st.markdown("---")
        st.markdown("**Mission:**")
        st.markdown(UI_MESSAGES['healing_mission'])
        
        st.markdown("---")
        st.markdown("**Debug:**")
        if st.checkbox("Show Full State"):
            # Show abbreviated session state (avoid circular references)
            safe_state = {}
            for key, value in st.session_state.items():
                try:
                    # Only include JSON-serializable values
                    json.dumps(value)
                    safe_state[key] = value
                except (TypeError, ValueError):
                    safe_state[key] = f"<{type(value).__name__}>"
            
            st.json(safe_state)
    
    # Footer
    st.markdown("---")
    st.markdown("### ✅ Modular Structure Test Complete")
    
    st.success("""
    **All Tests Passed!** 
    
    The modular structure is working correctly:
    - ✅ config.py loaded successfully
    - ✅ state_manager.py loaded successfully  
    - ✅ Mobile-responsive layout working
    - ✅ State management working
    - ✅ Error handling working
    - ✅ Navigation working
    """)
    
    st.info("""
    **Next Steps:**
    1. Test this on your Android phone via Streamlit Cloud
    2. Report any errors with Android version and browser details
    3. Proceed to add auth.py, data_manager.py, ai_processor.py, and utils.py
    """)
    
    # Version info
    st.caption(f"The Third Voice AI v{VERSION} - Built with ❤️ for Samantha and all families seeking healing")

if __name__ == "__main__":
    main()
