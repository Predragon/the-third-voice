import streamlit as st
from supabase import create_client, Client
import requests
import json
import datetime
import uuid

# ✅ Demo user fallback UUID (replace with real auth ID if available)
DEMO_USER_ID = "12345678-1234-1234-1234-123456789abc"

# ✅ Load secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
API_KEY = st.secrets["openrouter"]["api_key"]
API_URL = st.secrets["openrouter"].get("api_url", "https://openrouter.ai/api/v1/chat/completions")
AI_MODELS = json.loads(st.secrets["openrouter"]["models"])

# ✅ Supabase connection
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.success("Connected to Supabase successfully!")

# --- Load contacts & messages from Supabase ---
def load_supabase_history(user_id):
    try:
        response = (
            supabase.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp")
            .execute()
        )
        messages = response.data
        contacts = {}

        for msg in messages:
            name = msg["contact_name"]
            if name not in contacts:
                contacts[name] = {
                    "context": msg.get("context", "family"),
                    "history": []
                }

            contacts[name]["history"].append({
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
        return {}

# --- Initialize session state ---
def initialize_session():
    contacts = load_supabase_history(DEMO_USER_ID)

    defaults = {
        "token_validated": True,
        "api_key": API_KEY,
        "models": AI_MODELS,
        "contacts": contacts,
        "user_id": DEMO_USER_ID,
        "active_contact": None,
        "journal_entries": {},
        "feedback_data": {},
        "user_stats": {
            "total_messages": 0,
            "coached_messages": 0,
            "translated_messages": 0
        },
        "active_mode": None
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    # Set default contact if available
    if not st.session_state.active_contact and contacts:
        st.session_state.active_contact = list(contacts.keys())[0]

# --- Save message to Supabase ---
def save_message(contact_name, msg_type, original, result, model, sentiment, context, emotional_state):
    try:
        supabase.table("messages").insert({
            "contact_name": contact_name,
            "type": msg_type,
            "original": original,
            "result": result,
            "model": model,
            "sentiment": sentiment,
            "context": context,
            "user_id": st.session_state.user_id,
            "emotional_state": emotional_state,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"Could not save message: {e}")

# --- AI Message Request ---
def call_ai_model(prompt, context, model_name):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.warning(f"Error with model {model_name}: {e}")
        return None

# --- Main App Interface ---
def render_main():
    st.title("🎙️ The Third Voice — Emotional Intelligence Assistant")

    st.sidebar.header("👤 Contacts")
    contacts = st.session_state.contacts

    if contacts:
        selected = st.sidebar.radio(
            "Select contact",
            list(contacts.keys()),
            index=0 if not st.session_state.active_contact else list(contacts.keys()).index(st.session_state.active_contact)
        )
        st.session_state.active_contact = selected
        contact = contacts[selected]
    else:
        st.sidebar.info("No contacts yet. Add one below.")
        contact = None

    if st.sidebar.button("➕ Add Contact"):
        with st.sidebar.form("new_contact"):
            new_name = st.text_input("Contact Name")
            new_context = st.text_area("Relationship Context", "family, friend, partner...")
            submitted = st.form_submit_button("Add")
            if submitted and new_name:
                try:
                    supabase.table("contacts").insert({
                        "name": new_name,
                        "context": new_context,
                        "user_id": st.session_state.user_id
                    }).execute()
                    st.session_state.contacts[new_name] = {
                        "context": new_context,
                        "history": []
                    }
                    st.session_state.active_contact = new_name
                    st.success(f"Contact {new_name} added.")
                except Exception as e:
                    st.error(f"Failed to add contact: {e}")

    if contact:
        st.subheader(f"🧠 {st.session_state.active_contact} — {contact['context']}")
        st.markdown("### 💬 Conversation History")
        for msg in reversed(contact["history"][-10:]):
            with st.expander(f"[{msg['time']}] {msg['type'].capitalize()}"):
                st.markdown(f"**Original:** {msg['original']}")
                st.markdown(f"**AI Response:** {msg['result']}")
                st.caption(f"{msg['model']} | Sentiment: {msg['sentiment']}")

        st.markdown("### ✍️ New Message")
        with st.form("message_form"):
            msg_type = st.selectbox("Type", ["coach", "translate", "mediate"])
            original = st.text_area("Message")
            submitted = st.form_submit_button("Send")

            if submitted and original.strip():
                context = contact["context"]
                for model in AI_MODELS:
                    result = call_ai_model(original, context, model)
                    if result:
                        break

                if result:
                    save_message(
                        st.session_state.active_contact,
                        msg_type,
                        original,
                        result,
                        model,
                        sentiment="neutral",
                        context=context,
                        emotional_state="unknown"
                    )
                    st.session_state.contacts[st.session_state.active_contact]["history"].append({
                        "id": f"{msg_type}_{datetime.datetime.now().isoformat()}",
                        "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                        "type": msg_type,
                        "original": original,
                        "result": result,
                        "sentiment": "neutral",
                        "model": model
                    })
                    st.success("AI response added.")
                    st.experimental_rerun()
                else:
                    st.error("All model attempts failed.")

    else:
        st.info("Welcome! Add or select a contact to begin.")

# --- Run the app ---
initialize_session()
render_main()
