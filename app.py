"""
The Third Voice AI - Modular Entry Point
Streamlit application for relationship communication healing
Enhanced with streamlit-supabase-auth for reliable authentication
"""

import streamlit as st
from src.config.settings import init_app_config
from src.ui.app_controller import run_app

# Set page config first (must be the first Streamlit command)
st.set_page_config(
    page_title="The Third Voice AI",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize configuration
init_app_config()

# Run the application
if __name__ == "__main__":
    run_app()
else:
    # Also run when imported (for Streamlit Cloud deployment)
    run_app()
