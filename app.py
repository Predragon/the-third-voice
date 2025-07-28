import streamlit as st
from config import CONTEXTS
from state_manager import StateManager

def main():
    st.set_page_config(page_title="The Third Voice AI", page_icon="🎙️", layout="centered")
    state_manager = StateManager()
    st.title("🎙️ The Third Voice AI - Test")
    st.write("Testing modular structure")
    st.write(f"Contexts: {CONTEXTS}")
    st.write(f"State: {state_manager.state}")
    if st.button("Set Test State"):
        state_manager.set('test_key', 'test_value')
        st.write(f"Updated State: {state_manager.get('test_key')}")
    if st.button("Get User ID"):
        user_id = state_manager.get_current_user_id(None)  # No Supabase for testing
        st.write(f"User ID: {user_id}")

if __name__ == "__main__":
    main()
