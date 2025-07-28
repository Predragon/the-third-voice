import streamlit as st

class StateManager:
    def __init__(self):
        if 'state' not in st.session_state:
            st.session_state['state'] = {}
        self.state = st.session_state['state']

    def set(self, key, value):
        self.state[key] = value
        st.session_state['state'] = self.state

    def get(self, key, default=None):
        return self.state.get(key, default)

    def get_current_user_id(self, supabase):
        return self.get('user_id', None)