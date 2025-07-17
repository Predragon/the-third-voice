"""
The Third Voice - Coded with love and hope.
Created by Predrag Mirkovic, for Samantha and every family that deserves a second chance.
"""

import streamlit as st
import streamlit.components.v1 as components
import js_snippets
import json
import datetime

# Inject JS for persistence using the modular Python JS file
components.html(f"<script>{js_snippets.PERSISTENCE_JS}</script>", height=0)

# Hidden fields to connect to JS/localStorage
st.markdown('<input type="hidden" data-token="true" />', unsafe_allow_html=True)
st.markdown('<textarea style="display:none" data-history="true"></textarea>', unsafe_allow_html=True)
st.markdown('<textarea style="display:none" data-setup="true"></textarea>', unsafe_allow_html=True)

# Session defaults
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'setup' not in st.session_state:
    st.session_state['setup'] = {}
if "token_validated" not in st.session_state:
    st.session_state['token_validated'] = False

st.title("The Third Voice")

# Token gate
if not st.session_state['token_validated']:
    st.warning("🔐 Enter your token to continue.")
    token = st.text_input("Token:", type="password")
    if st.button("Validate"):
        if token and token.startswith("ttv-"):
            st.session_state['token_validated'] = True
            # Save token via JS for persistence
            components.html(f"<script>window.parent.postMessage({{type:'save',token:'{token}'}},'*');</script>", height=0)
            st.rerun()
        else:
            st.error("Invalid token")
    st.stop()

st.success("💚 Welcome! All data is stored only in your browser/device unless you export it.")

# Upload/restore history & setup
uploaded = st.file_uploader("📤 Upload your history and settings (JSON download):", type="json")
if uploaded:
    try:
        data = json.load(uploaded)
        st.session_state.history = data.get("history", [])
        st.session_state.setup = data.get("setup", {})
        # Save immediately to localStorage via JS
        components.html(
            f"<script>window.parent.postMessage({{type:'save',history:{json.dumps(st.session_state['history'])},setup:{json.dumps(st.session_state['setup'])}}},'*');</script>",
            height=0,
        )
        st.success("History and settings imported!")
    except:
        st.error("Invalid file format or file.")

# Add a message to history (for demo)
new_message = st.text_input("Add a message to history (demo):")
if st.button("Add message") and new_message:
    st.session_state['history'].append(
        {"timestamp": datetime.datetime.now().isoformat(), "message": new_message}
    )
    # Save through JS
    components.html(
        f"<script>window.parent.postMessage({{type:'save',history:{json.dumps(st.session_state['history'])}}},'*');</script>",
        height=0,
    )
    st.experimental_rerun()

st.header("Conversation History")
for i, entry in enumerate(reversed(st.session_state['history'])):
    st.write(f"{len(st.session_state['history'])-i}. [{entry['timestamp']}] {entry['message']}")

if st.button("Clear All History"):
    st.session_state['history'] = []
    components.html(
        "<script>window.parent.postMessage({type:'save',history:[]},'*');</script>", height=0
    )
    st.success("History cleared!")
    st.experimental_rerun()

st.header("Settings (Setup Data)")
if st.session_state['setup']:
    st.json(st.session_state['setup'])
else:
    st.info("No settings data. (Will appear here if imported/uploaded.)")

if st.button("Clear Setup"):
    st.session_state['setup'] = {}
    components.html(
        "<script>window.parent.postMessage({type:'save',setup:{}},'*');</script>", height=0
    )
    st.success("Setup/settings cleared!")
    st.experimental_rerun()

# Download/export
if st.button("Download my data"):
    payload = {
        "history": st.session_state['history'],
        "setup": st.session_state['setup'],
        "saved_at": datetime.datetime.now().isoformat()
    }
    st.download_button(
        label="📥 Click to download all history/settings",
        data=json.dumps(payload, indent=2),
        file_name="third_voice_history.json",
        mime="application/json",
    )

st.caption("Built with longing and hope. All your data stays only on your device unless you export it.")

