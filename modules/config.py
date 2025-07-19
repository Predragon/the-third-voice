# modules/config.py

import streamlit as st

# Secrets are securely stored in Streamlit Cloud
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

# Add other constants or API configs here
APP_TITLE = "The Third Voice"
APP_ICON = "🎙️"
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
