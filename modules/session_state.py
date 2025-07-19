# modules/session_state.py

import streamlit as st
from modules.config import OPENROUTER_API_KEY

defaults = {
    'token_validated': False,
    'api_key': OPENROUTER_API_KEY,
    'count': 0,
    'history': [],
    'active_msg': '',
    'active_ctx': 'general',
}

def init_session():
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
