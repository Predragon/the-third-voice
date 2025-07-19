# app.py

import streamlit as st
import requests
import json

from modules.config import APP_TITLE, APP_ICON, CONTEXTS
from modules.session_state import init_session
from modules.prompts import get_prompt
from modules.utils import format_message

# App setup
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
st.title(APP_TITLE)

# Session state
init_session()

# Sidebar
st.sidebar.header("Settings")
st.session_state["active_ctx"] = st.sidebar.selectbox("Select context:", CONTEXTS)
st.session_state["api_key"] = st.sidebar.text_input("OpenRouter API Key", type="password", value=st.session_state["api_key"])

# Main interface
user_input = st.text_area("You:", height=100, key="user_msg")

if st.button("Send"):
    if not st.session_state["api_key"]:
        st.warning("Please enter your OpenRouter API key.")
    elif not user_input.strip():
        st.warning("Message cannot be empty.")
    else:
        # Generate and send prompt
        prompt = get_prompt(st.session_state["active_ctx"], user_input)
        headers = {
            "Authorization": f"Bearer {st.session_state['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "openchat/openchat-7b:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(payload))
            reply = response.json()["choices"][0]["message"]["content"]
            st.session_state["history"].append({"user": user_input, "assistant": reply})
        except Exception as e:
            st.error(f"Error: {e}")

# Display chat history
st.divider()
for chat in reversed(st.session_state["history"]):
    st.markdown(format_message("🧍 You", chat["user"]), unsafe_allow_html=True)
    st.markdown(format_message("🤖 Third Voice", chat["assistant"]), unsafe_allow_html=True)
