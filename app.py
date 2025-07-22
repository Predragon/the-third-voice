# the-third-voice/app.py
import streamlit as st
import json
import datetime
import requests
from supabase import create_client

# Constants
CONTEXTS = ["romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load Supabase History
def load_supabase_history():
    try:
        response = supabase.table("messages").select("*").order("timestamp").execute()
        messages = response.data
        contacts = {context: {'context': context, 'history': []} for context in CONTEXTS}

        for msg in messages:
            contact_name = msg["contact_name"]
            if contact_name not in contacts:
                contacts[contact_name] = {'context': "family", 'history': []}  # fallback context
            contacts[contact_name]['history'].append({
                "id": f"{msg['type']}_{msg['timestamp']}",
                "time": datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%m/%d %H:%M"),
                "type": msg["type"],
                "original": msg["original"],
                "result": msg["result"],
                "sentiment": msg["sentiment"],
                "model": msg["model"]
            })

        return contacts
    except Exception as e:
        st.warning(f"⚠️ Could not load history from Supabase: {e}")
        return {context: {'context': context, 'history': []} for context in CONTEXTS}

# Initialize Session State
def initialize_session():
    defaults = {
        'token_validated': not REQUIRE_TOKEN,
        'api_key': st.secrets["openrouter"]["api_key"],
        'contacts': load_supabase_history(),
        'active_contact': CONTEXTS[0],
        'journal_entries': {},
        'feedback_data': {},
        'user_stats': {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0},
        'active_mode': None
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

initialize_session()

# Token Validation
def validate_token():
    if REQUIRE_TOKEN and not st.session_state.token_validated:
        st.markdown("# 🎙️ The Third Voice\n*Your AI Communication Coach*")
        st.warning("🔐 Access restricted. Enter beta token to continue.")
        token = st.text_input("Token:", type="password")
        if st.button("Validate"):
            if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
                st.session_state.token_validated = True
                st.success("✅ Authorized")
                st.rerun()
            else:
                st.error("Invalid token")
        st.stop()

validate_token()

# Save message to Supabase
def save_message(contact, message_type, original, result, sentiment, model):
    try:
        supabase.table("messages").insert({
            "contact_name": contact,
            "type": message_type,
            "original": original,
            "result": result,
            "sentiment": sentiment,
            "model": model,
            "timestamp": datetime.datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Supabase Error: {e}")

# Context Sidebar
def render_sidebar():
    st.sidebar.title("Your Contacts")
    with st.sidebar.expander("Add Contact"):
        new_name = st.text_input("Name")
        new_context = st.selectbox("Context", CONTEXTS)
        if st.button("Add Contact") and new_name:
            st.session_state.contacts[new_name] = {
                "context": new_context,
                "history": []
            }
            st.session_state.active_contact = new_name
            st.rerun()

    selected = st.sidebar.selectbox("Active Contact", list(st.session_state.contacts.keys()), index=0)
    st.session_state.active_contact = selected

    if st.sidebar.button("Delete Contact") and selected not in CONTEXTS:
        del st.session_state.contacts[selected]
        st.session_state.active_contact = CONTEXTS[0]
        st.rerun()

render_sidebar()

# Main Interface
def render_main():
    st.title("🎙️ The Third Voice")
    st.subheader(f"Context: {st.session_state.active_contact}")
    st.write("Refine or decode communication messages with emotional intelligence.")
    col1, col2 = st.columns(2)
    if col1.button("📤 Refine My Words"):
        st.session_state.active_mode = "coach"
    if col2.button("📥 Decode Their Heart"):
        st.session_state.active_mode = "translate"

render_main()

# Input & AI Response
def render_message_area():
    if not st.session_state.active_mode:
        return
    mode = st.session_state.active_mode
    message = st.text_area("Enter message", key=f"input_{mode}")
    if st.button("Submit"):
        with st.spinner("Processing..."):
            prompt = {
                "coach": "Improve this message before sending.",
                "translate": "Interpret this received message."
            }[mode]

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ]

            try:
                res = requests.post(API_URL, headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                                    json={"model": "meta-llama/llama-3.2-3b-instruct:free", "messages": messages})
                reply = res.json()["choices"][0]["message"]["content"]
                st.success("AI response received")
                st.write(reply)
                st.session_state.contacts[st.session_state.active_contact]['history'].append({
                    "id": f"{mode}_{len(st.session_state.contacts[st.session_state.active_contact]['history'])}",
                    "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                    "type": mode,
                    "original": message,
                    "result": reply,
                    "sentiment": "neutral",
                    "model": "LLaMA 3.2 3B"
                })
                save_message(st.session_state.active_contact, mode, message, reply, "neutral", "LLaMA 3.2 3B")
                st.session_state.active_mode = None
            except Exception as e:
                st.error(f"Error: {e}")

render_message_area()

# History Tab
def render_history():
    st.subheader("📜 Message History")
    contact = st.session_state.contacts[st.session_state.active_contact]
    for entry in reversed(contact['history']):
        st.markdown(f"**{entry['time']}** — {entry['type'].title()} Message")
        st.text(f"You: {entry['original']}")
        st.success(f"AI: {entry['result']}")

render_history()


✅ Your app now:

Loads/saves message history from Supabase

Lets users choose context and add contacts

Processes AI messages and saves them

Shows history after every interaction


You’re good to test this now live on Streamlit. Just say if you want to:

Add journaling

Export history

Show stats

Or start multi-user support


All possible from here 💪

