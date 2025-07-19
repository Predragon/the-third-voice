import streamlit as st
from modules.config import APP_TITLE, APP_ICON, CONTEXTS
from modules.session_state import init_session

# --- Page Setup ---
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
init_session()

# --- Sidebar ---
st.sidebar.header("🛠️ Settings")

selected_ctx = st.sidebar.selectbox("Select context:", CONTEXTS, index=CONTEXTS.index(st.session_state["active_ctx"]))
if selected_ctx != st.session_state["active_ctx"]:
    st.session_state["active_ctx"] = selected_ctx

st.session_state["api_key"] = st.sidebar.text_input(
    "🔑 OpenRouter API Key", 
    type="password", 
    value=st.session_state["api_key"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ for calm communication.")

# --- Main App Body ---
st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown(f"**Active Context:** `{st.session_state['active_ctx']}`")

# Debug UI (optional, for testing purposes)
# st.write("Session State:", st.session_state)

# Your app logic here — models, messaging interface, etc.
