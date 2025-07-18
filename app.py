# app.py
import streamlit as st
import json
import datetime
import requests
from pathlib import Path

# ========================
# CONSTANTS & CONFIG
# ========================
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUIRE_TOKEN = False

# ========================
# SESSION STATE
# ========================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
        'contacts': {'General': {'context': 'general', 'history': []}},
        'active_contact': 'General',
        'active_mode': None,
        'journal_entries': {},
        'feedback_data': {},
        'user_stats': {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0}
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

# ========================
# CORE FUNCTIONS
# ========================
def get_ai_response(message, context, is_received=False):
    """Get AI response from API"""
    if not st.session_state.api_key:
        return {"error": "API key missing"}
    
    prompts = {
        "general": "You're an emotional intelligence coach helping improve communication...",
        "romantic": "Help rephrase romantic messages with empathy and clarity...",
        # ... other contexts ...
    }
    
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {st.session_state.api_key}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{
                    "role": "system", 
                    "content": prompts.get(context, prompts["general"])
                }, {
                    "role": "user", 
                    "content": message
                }]
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ========================
# UI COMPONENTS
# ========================
def render_sidebar():
    """Left sidebar for contacts and tools"""
    with st.sidebar:
        st.title("🎙️ Third Voice")
        st.subheader("Your Contacts")
        
        # Contact list
        for name in st.session_state.contacts:
            if st.button(
                f"👤 {name}",
                key=f"contact_{name}",
                use_container_width=True,
                type="primary" if name == st.session_state.active_contact else "secondary"
            ):
                st.session_state.active_contact = name
                st.rerun()
        
        st.divider()
        
        # Add new contact
        with st.expander("➕ Add Contact"):
            new_name = st.text_input("Name")
            new_context = st.selectbox("Relationship", CONTEXTS)
            if st.button("Save"):
                st.session_state.contacts[new_name] = {'context': new_context, 'history': []}
                st.rerun()

def render_main():
    """Primary chat interface"""
    st.header(f"💬 Chat with {st.session_state.active_contact}")
    
    # Message history
    contact = st.session_state.contacts[st.session_state.active_contact]
    for msg in contact['history']:
        with st.chat_message("user" if msg['type'] == 'sent' else "assistant"):
            st.write(msg['content'])
            st.caption(f"{msg['time']} • {msg.get('model', '')}")

    # Input area
    mode = st.radio(
        "Mode:",
        ["📝 Compose", "🔍 Analyze"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if prompt := st.chat_input("Type your message..."):
        result = get_ai_response(prompt, contact['context'])
        if "error" not in result:
            contact['history'].append({
                'type': 'sent',
                'content': prompt,
                'time': datetime.datetime.now().strftime("%H:%M"),
                'model': result.get('model', '')
            })
            st.rerun()

# ========================
# MAIN APP
# ========================
def main():
    # Page config
    st.set_page_config(
        page_title="Third Voice",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session
    init_session_state()
    
    # Apply custom CSS
    st.markdown("""
    <style>
    .stChatInput {position: fixed; bottom: 2rem;}
    .stButton button {transition: all 0.2s ease;}
    .stButton button:hover {transform: scale(1.02);}
    </style>
    """, unsafe_allow_html=True)
    
    # Render UI
    render_sidebar()
    render_main()

if __name__ == "__main__":
    main()
